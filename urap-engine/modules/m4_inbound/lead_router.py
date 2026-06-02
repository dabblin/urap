"""Module IV — Inbound Lead Capture & Distribution (Sprint 5)."""
import os
import uuid
import logging
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")


def _db():
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_KEY)


# ── Data models ───────────────────────────────────────────────────────────────

@dataclass
class InboundLead:
    lead_id: str
    tenant_id: str
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: str = ""
    company: str = ""
    title: str = ""
    ip_address: str = ""
    country_code: str = "US"
    source: str = "web"
    intent_signals: list = field(default_factory=list)
    raw: dict = field(default_factory=dict)
    created_at: str = ""


@dataclass
class PreviewAttributes:
    """Anonymized lead attributes for ping-post preview (no PII)."""
    preview_id: str
    company_size: str       # "1-10", "11-50", "51-200", "201-500", "500+"
    industry: str
    title_level: str        # "C-Suite", "VP", "Director", "Manager", "IC"
    intent_count: int
    country_code: str
    source: str
    expires_at: str         # ISO timestamp — preview expires in 5 min


@dataclass
class ClaimResult:
    success: bool
    lead_id: str
    preview_id: str
    pii_released: bool
    stripe_event_fired: bool
    error: str = ""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _infer_company_size(enriched: dict) -> str:
    headcount = enriched.get("headcount") or enriched.get("employee_count") or 0
    try:
        n = int(headcount)
    except (ValueError, TypeError):
        return "unknown"
    if n <= 10: return "1-10"
    if n <= 50: return "11-50"
    if n <= 200: return "51-200"
    if n <= 500: return "201-500"
    return "500+"


def _infer_title_level(title: str) -> str:
    t = title.lower()
    if any(k in t for k in ("ceo", "cto", "cfo", "coo", "ciso", "cmo", "chief", "president", "founder")):
        return "C-Suite"
    if "vp" in t or "vice president" in t:
        return "VP"
    if "director" in t:
        return "Director"
    if "manager" in t or "head of" in t or "lead" in t:
        return "Manager"
    return "IC"


# ── Service ───────────────────────────────────────────────────────────────────

class LeadRouterService:
    """
    Handles inbound lead capture, ping-post distribution, and Twilio geo-routing.
    Table: urap_lead_distribution (created by 004_sprint5_lead_distribution.sql)
    """

    # Active previews held in memory (preview_id → lead_id + expiry).
    # In production this should be Redis; in-process is fine for single-replica Cloud Run.
    _preview_cache: dict[str, dict] = {}

    async def capture(
        self,
        tenant_id: str,
        first_name: str = "",
        last_name: str = "",
        email: str = "",
        phone: str = "",
        company: str = "",
        title: str = "",
        ip_address: str = "",
        source: str = "web",
        raw: dict | None = None,
    ) -> InboundLead:
        """
        Step 1 of ping-post: receive inbound lead, enrich, store in Supabase.
        Returns InboundLead with lead_id assigned.
        """
        from tier3.twilio.client import geolocate_country
        country_code = geolocate_country(ip_address) if ip_address else "US"

        lead_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        # Attempt lightweight enrichment from cache
        enriched: dict = {}
        if email or company:
            try:
                from modules.m1_intelligence.enrichment import EnrichmentService
                svc = EnrichmentService()
                domain = email.split("@")[-1] if "@" in email else company
                result = await svc.enrich_contact(
                    tenant_id=tenant_id,
                    first_name=first_name,
                    last_name=last_name,
                    domain=domain,
                    title=title,
                )
                if result:
                    enriched = result
            except Exception as exc:
                logger.warning("[lead_router] enrichment skipped: %s", exc)

        intent_signals = enriched.get("intent_signals") or []

        row = {
            "id": lead_id,
            "tenant_id": tenant_id,
            "first_name": first_name or enriched.get("first_name", ""),
            "last_name": last_name or enriched.get("last_name", ""),
            "email": email or enriched.get("email", ""),
            "phone": phone or enriched.get("phone", ""),
            "company": company or enriched.get("company", ""),
            "title": title or enriched.get("title", ""),
            "ip_address": ip_address,
            "country_code": country_code,
            "source": source,
            "intent_signals": intent_signals,
            "enriched_data": enriched,
            "raw_payload": raw or {},
            "status": "captured",
            "created_at": now,
        }

        try:
            _db().table("urap_lead_distribution").insert(row).execute()
        except Exception as exc:
            logger.error("[lead_router] insert failed: %s", exc)

        return InboundLead(
            lead_id=lead_id,
            tenant_id=tenant_id,
            first_name=row["first_name"],
            last_name=row["last_name"],
            email=row["email"],
            phone=row["phone"],
            company=row["company"],
            title=row["title"],
            ip_address=ip_address,
            country_code=country_code,
            source=source,
            intent_signals=intent_signals,
            raw=raw or {},
            created_at=now,
        )

    def preview(self, lead: InboundLead) -> PreviewAttributes:
        """
        Step 2 of ping-post: build anonymized preview, cache with 5-min TTL.
        Returns PreviewAttributes — no PII exposed.
        """
        from datetime import timedelta
        preview_id = str(uuid.uuid4())
        expires_at = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()

        self._preview_cache[preview_id] = {
            "lead_id": lead.lead_id,
            "tenant_id": lead.tenant_id,
            "expires_at": expires_at,
        }

        # Attempt to get company size from Supabase enrichment cache
        enriched: dict = {}
        try:
            result = _db().table("urap_contacts").select("*").eq("email", lead.email).limit(1).execute()
            if result.data:
                enriched = result.data[0]
        except Exception:
            pass

        return PreviewAttributes(
            preview_id=preview_id,
            company_size=_infer_company_size(enriched),
            industry=enriched.get("industry") or "Unknown",
            title_level=_infer_title_level(lead.title),
            intent_count=len(lead.intent_signals),
            country_code=lead.country_code,
            source=lead.source,
            expires_at=expires_at,
        )

    async def claim(self, preview_id: str, buyer_tenant_id: str) -> ClaimResult:
        """
        Step 3 of ping-post: buyer claims lead — release PII, fire Stripe metered event.
        Returns ClaimResult.
        """
        cached = self._preview_cache.get(preview_id)
        if not cached:
            return ClaimResult(
                success=False, lead_id="", preview_id=preview_id,
                pii_released=False, stripe_event_fired=False,
                error="Preview not found or expired",
            )

        # Check expiry
        expiry = datetime.fromisoformat(cached["expires_at"])
        if datetime.now(timezone.utc) > expiry:
            del self._preview_cache[preview_id]
            return ClaimResult(
                success=False, lead_id="", preview_id=preview_id,
                pii_released=False, stripe_event_fired=False,
                error="Preview expired",
            )

        lead_id = cached["lead_id"]
        del self._preview_cache[preview_id]

        # Mark as claimed in Supabase
        try:
            _db().table("urap_lead_distribution").update({
                "status": "claimed",
                "claimed_by_tenant_id": buyer_tenant_id,
                "claimed_at": datetime.now(timezone.utc).isoformat(),
            }).eq("id", lead_id).execute()
        except Exception as exc:
            logger.error("[lead_router] claim update failed: %s", exc)

        # Fire Stripe metered event (qualified lead billing)
        stripe_fired = False
        try:
            from services.stripe_metered import report_lead_qualified
            report_lead_qualified(tenant_id=buyer_tenant_id, lead_id=lead_id)
            stripe_fired = True
        except Exception as exc:
            logger.warning("[lead_router] stripe metered event skipped: %s", exc)

        return ClaimResult(
            success=True,
            lead_id=lead_id,
            preview_id=preview_id,
            pii_released=True,
            stripe_event_fired=stripe_fired,
        )

    def get_lead_pii(self, lead_id: str) -> dict:
        """Retrieve full PII record for a claimed lead."""
        try:
            result = _db().table("urap_lead_distribution").select("*").eq("id", lead_id).limit(1).execute()
            if result.data:
                row = result.data[0]
                return {
                    "lead_id": row["id"],
                    "first_name": row.get("first_name", ""),
                    "last_name": row.get("last_name", ""),
                    "email": row.get("email", ""),
                    "phone": row.get("phone", ""),
                    "company": row.get("company", ""),
                    "title": row.get("title", ""),
                    "country_code": row.get("country_code", ""),
                    "intent_signals": row.get("intent_signals", []),
                }
        except Exception as exc:
            logger.error("[lead_router] get_lead_pii error: %s", exc)
        return {}

    def list_recent(self, tenant_id: str, limit: int = 20) -> list[dict]:
        """List recently captured leads for a tenant (no PII in listing)."""
        try:
            result = (
                _db().table("urap_lead_distribution")
                .select("id,company,title,country_code,source,status,intent_signals,created_at")
                .eq("tenant_id", tenant_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data or []
        except Exception as exc:
            logger.error("[lead_router] list_recent error: %s", exc)
            return []
