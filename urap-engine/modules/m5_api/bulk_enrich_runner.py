"""Bulk enrichment runner — CSV list or ICP-filter batch jobs."""
import os
import csv
import io
import uuid
import logging
from datetime import datetime, timezone
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")


def _db():
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_KEY)


@dataclass
class BulkJob:
    job_id: str
    tenant_id: str
    source: str          # "csv" | "icp"
    total: int
    enriched: int
    failed: int
    status: str          # "running" | "complete" | "error"
    results: list = field(default_factory=list)
    error: str = ""
    created_at: str = ""


class BulkEnrichRunner:
    async def run_csv(self, tenant_id: str, csv_text: str, limit: int = 100) -> BulkJob:
        """
        Enrich contacts from CSV text.
        Expected columns (order-insensitive): first_name, last_name, domain (or email or company).
        Returns a BulkJob with per-row results.
        """
        from modules.m1_intelligence.enrichment import EnrichmentService
        svc = EnrichmentService()
        job_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        rows = self._parse_csv(csv_text, limit)
        results = []
        enriched_count = 0
        failed_count = 0

        for row in rows:
            domain = row.get("domain") or self._domain_from_email(row.get("email", "")) or row.get("company", "")
            if not domain:
                results.append({**row, "_status": "skipped", "_reason": "no domain/email/company"})
                failed_count += 1
                continue
            try:
                contact = await svc.enrich_contact(
                    tenant_id=tenant_id,
                    first_name=row.get("first_name", ""),
                    last_name=row.get("last_name", ""),
                    domain=domain,
                    title=row.get("title", ""),
                )
                if contact:
                    results.append({**row, **contact, "_status": "enriched"})
                    enriched_count += 1
                else:
                    results.append({**row, "_status": "not_found"})
                    failed_count += 1
            except Exception as exc:
                results.append({**row, "_status": "error", "_reason": str(exc)})
                failed_count += 1

        job = BulkJob(
            job_id=job_id,
            tenant_id=tenant_id,
            source="csv",
            total=len(rows),
            enriched=enriched_count,
            failed=failed_count,
            status="complete",
            results=results,
            created_at=now,
        )
        self._store_job(job)
        return job

    async def run_icp(self, tenant_id: str, domain: str, limit: int = 50) -> BulkJob:
        """
        Bulk-enrich all contacts at a domain via the enrichment waterfall.
        Wraps the existing /enrich/bulk endpoint logic.
        """
        from modules.m1_intelligence.enrichment import EnrichmentService
        svc = EnrichmentService()
        job_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        results = []
        enriched_count = 0
        failed_count = 0

        try:
            contacts = await svc.bulk_enrich_domain(
                tenant_id=tenant_id,
                domain=domain,
                limit=min(limit, 100),
            )
            for c in contacts:
                if c.get("email"):
                    results.append({**c, "_status": "enriched"})
                    enriched_count += 1
                else:
                    results.append({**c, "_status": "partial"})
                    failed_count += 1
        except Exception as exc:
            logger.error("[bulk_enrich] run_icp error: %s", exc)
            job = BulkJob(
                job_id=job_id, tenant_id=tenant_id, source="icp",
                total=0, enriched=0, failed=0, status="error",
                error=str(exc), created_at=now,
            )
            self._store_job(job)
            return job

        job = BulkJob(
            job_id=job_id,
            tenant_id=tenant_id,
            source="icp",
            total=len(results),
            enriched=enriched_count,
            failed=failed_count,
            status="complete",
            results=results,
            created_at=now,
        )
        self._store_job(job)
        return job

    def get_job(self, job_id: str, tenant_id: str) -> dict | None:
        """Retrieve a bulk job record from Supabase."""
        try:
            result = (
                _db().table("urap_bulk_jobs")
                .select("*")
                .eq("id", job_id)
                .eq("tenant_id", tenant_id)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as exc:
            logger.error("[bulk_enrich] get_job error: %s", exc)
            return None

    def list_jobs(self, tenant_id: str, limit: int = 20) -> list[dict]:
        """List recent bulk jobs for a tenant (summary only — no per-row results)."""
        try:
            result = (
                _db().table("urap_bulk_jobs")
                .select("id,source,total,enriched,failed,status,created_at")
                .eq("tenant_id", tenant_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data or []
        except Exception as exc:
            logger.error("[bulk_enrich] list_jobs error: %s", exc)
            return []

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _parse_csv(self, csv_text: str, limit: int) -> list[dict]:
        rows = []
        try:
            reader = csv.DictReader(io.StringIO(csv_text.strip()))
            for i, row in enumerate(reader):
                if i >= limit:
                    break
                rows.append({k.strip().lower(): v.strip() for k, v in row.items()})
        except Exception as exc:
            logger.error("[bulk_enrich] csv parse error: %s", exc)
        return rows

    def _domain_from_email(self, email: str) -> str:
        if "@" in email:
            return email.split("@")[-1]
        return ""

    def _store_job(self, job: BulkJob) -> None:
        try:
            _db().table("urap_bulk_jobs").insert({
                "id": job.job_id,
                "tenant_id": job.tenant_id,
                "source": job.source,
                "total": job.total,
                "enriched": job.enriched,
                "failed": job.failed,
                "status": job.status,
                "results": job.results[:200],  # cap stored results at 200 rows
                "error": job.error,
                "created_at": job.created_at,
            }).execute()
        except Exception as exc:
            logger.warning("[bulk_enrich] store_job failed: %s", exc)
