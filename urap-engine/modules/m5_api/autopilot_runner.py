"""Autopilot runner — cron-triggered Warp Mode scheduler (Sprint 6 full implementation)."""
import asyncio
import os
import logging
import math
from datetime import datetime, timezone
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")

UNSUBSCRIBE_PAUSE_THRESHOLD = 0.05   # auto-pause if >5% unsubscribe rate in last run
DEFAULT_DAILY_SEND_LIMIT    = 50
DEMO_CTA_URL = (
    "https://dabblin.com/demo/"
    "?utm_source=urap&utm_medium=email&utm_campaign=autopilot&utm_content=demo_cta"
)


def build_outreach_html(body_html: str) -> str:
    """Add one explicit tracked CTA and the sender signature."""
    cta = (
        '<p><a href="'
        f"{DEMO_CTA_URL}"
        '" style="color:#2563eb; font-weight:600;">'
        "Hear how the AI handles an incoming call"
        "</a></p>"
    )
    signature = """<br><br>
<p style="margin:0; font-size:14px; color:#333;"><strong>Dennis Day II</strong><br>
<span style="color:#666;">CAIO, Dabblin Cloud Technologies</span><br>
dabblin.com | 703.344.8307</p>
"""
    return f"{body_html}{cta}{signature}"


def _db():
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_KEY)


@dataclass
class AutopilotRunResult:
    tenant_id: str
    job_id: str
    leads_found: int
    sequences_queued: int
    skipped_deduped: int
    paused: bool
    pause_reason: str
    error: str = ""
    emails_sent: int = 0
    emails_failed: int = 0
    campaign_id: str = ""
    sector_stats: dict[str, int] = field(default_factory=dict)


class AutopilotRunner:
    async def enable(
        self,
        tenant_id: str,
        icp: dict,
        schedule_hours: int = 24,
        route_after_warp: bool = False,
        route_marketplace_id: str = "",
        route_min_score: int = 60,
    ) -> dict:
        """
        Save or update autopilot config for a tenant. Upsert on tenant_id.
        schedule_hours: run interval (24 = daily, 12 = every 12h, etc.)
        route_after_warp: if True, dispatch newly found leads to a marketplace after each Warp run.
        """
        try:
            row = {
                "tenant_id": tenant_id,
                "enabled": True,
                "icp": icp,
                "schedule_hours": max(1, schedule_hours),
                "daily_send_limit": DEFAULT_DAILY_SEND_LIMIT,
                "route_after_warp": route_after_warp,
                "route_marketplace_id": route_marketplace_id,
                "route_min_score": route_min_score,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            existing = (
                _db().table("urap_autopilot_configs")
                .select("id")
                .eq("tenant_id", tenant_id)
                .limit(1)
                .execute()
            )
            if existing.data:
                _db().table("urap_autopilot_configs").update(row).eq("tenant_id", tenant_id).execute()
            else:
                _db().table("urap_autopilot_configs").insert(row).execute()
            return {"success": True, "enabled": True, "schedule_hours": schedule_hours}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def disable(self, tenant_id: str) -> dict:
        """Disable autopilot for a tenant."""
        try:
            _db().table("urap_autopilot_configs").update({
                "enabled": False,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }).eq("tenant_id", tenant_id).execute()
            return {"success": True, "enabled": False}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def get_config(self, tenant_id: str) -> dict | None:
        """Return autopilot config for a tenant.

        Falls back to the AUTOPILOT_CONFIG_B64 env var (base64-encoded JSON,
        same shape as a urap_autopilot_configs row) while that table does not
        exist in Supabase — see supabase/migrations/20260717_autopilot_configs.sql.
        """
        try:
            result = (
                _db().table("urap_autopilot_configs")
                .select("*")
                .eq("tenant_id", tenant_id)
                .limit(1)
                .execute()
            )
            if result.data:
                return result.data[0]
        except Exception as exc:
            logger.warning("[autopilot] config table unavailable, trying env fallback: %s", exc)
        raw = os.getenv("AUTOPILOT_CONFIG_B64", "") or os.getenv("AUTOPILOT_CONFIG", "")
        if raw:
            try:
                import base64
                import json
                try:
                    decoded = base64.b64decode(raw).decode()
                except Exception:
                    decoded = raw
                cfg = json.loads(decoded)
                if cfg.get("tenant_id", tenant_id) == tenant_id:
                    return cfg
            except Exception as exc:
                logger.error("[autopilot] env config parse error: %s", exc)
        return None

    async def run(self, tenant_id: str) -> AutopilotRunResult:
        """
        Execute one Autopilot cycle for a tenant.
        Called by Cloud Scheduler (or POST /autopilot/run endpoint).
        Steps:
        1. Load config — skip if disabled
        2. Check unsubscribe rate — pause if above threshold
        3. Run Warp Mode job (deduped against existing active/replied leads)
        4. Enforce daily send throttle
        5. Update last_run_at + stats
        """
        config = self.get_config(tenant_id)
        if not config or not config.get("enabled"):
            return AutopilotRunResult(
                tenant_id=tenant_id, job_id="", leads_found=0,
                sequences_queued=0, skipped_deduped=0,
                paused=False, pause_reason="", error="Autopilot not enabled",
            )

        # Unsubscribe rate check
        unsub_rate = self._unsubscribe_rate(tenant_id)
        if unsub_rate > UNSUBSCRIBE_PAUSE_THRESHOLD:
            await self.disable(tenant_id)
            reason = f"Unsubscribe rate {unsub_rate:.1%} exceeded {UNSUBSCRIBE_PAUSE_THRESHOLD:.0%} threshold"
            self._log_run(tenant_id, {
                "leads_found": 0, "sequences_queued": 0,
                "skipped_deduped": 0, "paused": True, "pause_reason": reason,
            })
            return AutopilotRunResult(
                tenant_id=tenant_id, job_id="", leads_found=0,
                sequences_queued=0, skipped_deduped=0,
                paused=True, pause_reason=reason,
            )

        icp = config.get("icp", {})
        daily_limit = config.get("daily_send_limit", DEFAULT_DAILY_SEND_LIMIT)

        # Cap Warp Mode lead limit by remaining daily send budget
        sent_today = self._sent_today(tenant_id)
        remaining = max(0, daily_limit - sent_today)
        if remaining == 0:
            reason = f"Daily send limit {daily_limit} reached"
            return AutopilotRunResult(
                tenant_id=tenant_id, job_id="", leads_found=0,
                sequences_queued=0, skipped_deduped=0,
                paused=False, pause_reason=reason,
            )

        sectors = [sector for sector in (icp.get("sectors") or []) if sector]
        if not sectors and icp.get("keywords"):
            sectors = [icp["keywords"]]

        # Source fresh leads by keyword ICP (Apollo discovery), then dedup
        leads: list[dict] = []
        skipped_deduped = 0
        sector_stats: dict[str, int] = {sector: 0 for sector in sectors}

        if sectors:
            valid_sectors = sectors
            configured_sector_limit = max(1, int(icp.get("limit", 25)))
            sector_limit = min(
                configured_sector_limit,
                max(1, math.ceil(remaining / len(valid_sectors))),
            )
            source_semaphore = asyncio.Semaphore(3)

            async def source_sector(sector: str) -> tuple[str, list[dict]]:
                sector_icp = {**icp, "keywords": sector, "limit": sector_limit}
                try:
                    async with source_semaphore:
                        return sector, await self._source_leads(sector_icp)
                except Exception as exc:
                    logger.error("[autopilot] lead sourcing error for %s: %s", sector, exc)
                    return sector, []

            sourced = await asyncio.gather(*(source_sector(sector) for sector in valid_sectors))
            all_sourced_leads = [
                {**lead, "_autopilot_sector": sector}
                for sector, sector_leads in sourced
                for lead in sector_leads
            ]
            deduped_leads, skipped_deduped = self._dedup_leads(tenant_id, all_sourced_leads)

            # Round-robin the deduped sector queues so one high-yield sector cannot
            # consume the entire daily budget before the other sectors are included.
            sector_queues = {
                sector: [
                    lead for lead in deduped_leads
                    if lead.get("_autopilot_sector") == sector
                ]
                for sector in valid_sectors
            }
            sector_offsets = {sector: 0 for sector in valid_sectors}
            while len(leads) < remaining:
                added = False
                for sector in valid_sectors:
                    offset = sector_offsets[sector]
                    queue = sector_queues[sector]
                    if offset >= len(queue):
                        continue
                    leads.append(queue[offset])
                    sector_offsets[sector] = offset + 1
                    sector_stats[sector] += 1
                    added = True
                    if len(leads) >= remaining:
                        break
                if not added:
                    break

            if not leads:
                reason = "No new leads after dedup" if skipped_deduped else ""
                return AutopilotRunResult(
                    tenant_id=tenant_id, job_id="", leads_found=0,
                    sequences_queued=0, skipped_deduped=skipped_deduped,
                    paused=False, pause_reason=reason,
                    error="" if skipped_deduped else "No leads found for ICP sectors/keywords",
                    sector_stats=sector_stats,
                )

        # Run Warp Mode (copy generation; enrichment fallback for domain ICPs)
        try:
            from modules.m3_agents.warp_mode import WarpModeAgent
            warp = WarpModeAgent()
            warp_icp = {**icp, "limit": min(len(leads), remaining)} if leads else icp
            result = await warp.run_job(icp=warp_icp, tenant_id=tenant_id, leads=leads or None)
        except Exception as exc:
            logger.error("[autopilot] warp run error: %s", exc)
            return AutopilotRunResult(
                tenant_id=tenant_id, job_id="", leads_found=0,
                sequences_queued=0, skipped_deduped=skipped_deduped,
                paused=False, pause_reason="", error=str(exc),
            )

        # Send the generated emails and record per-send rows
        emails_sent = emails_failed = 0
        campaign_id = ""
        generated = getattr(result, "generated", None) or []
        if generated:
            try:
                emails_sent, emails_failed, campaign_id = await self._send_generated(
                    tenant_id=tenant_id, icp=icp, generated=generated,
                )
            except Exception as exc:
                logger.error("[autopilot] send error: %s", exc)

        run_stats = {
            "leads_found": result.leads_found,
            "sequences_queued": result.sequences_queued,
            "skipped_deduped": skipped_deduped,
            "emails_sent": emails_sent,
            "emails_failed": emails_failed,
            "campaign_id": campaign_id,
            "sector_stats": sector_stats,
            "paused": False,
            "pause_reason": "",
        }
        self._log_run(tenant_id, run_stats)

        # Route-after-Warp: dispatch qualifying leads to configured marketplace
        route_marketplace_id = config.get("route_marketplace_id", "")
        if config.get("route_after_warp") and route_marketplace_id:
            try:
                from modules.m4_inbound.marketplace_router import MarketplaceRouter
                route_min_score = config.get("route_min_score", 60)
                router = MarketplaceRouter()
                # Pull recently enriched leads above the score threshold
                leads_to_route = self._get_routable_leads(
                    tenant_id=tenant_id,
                    min_score=route_min_score,
                    limit=result.leads_found,
                )
                if leads_to_route:
                    await router.dispatch(
                        tenant_id=tenant_id,
                        marketplace_id=route_marketplace_id,
                        leads=leads_to_route,
                        ping_post=False,
                    )
                    logger.info(
                        "[autopilot] route-after-warp dispatched %d leads → %s",
                        len(leads_to_route), route_marketplace_id,
                    )
            except Exception as exc:
                logger.warning("[autopilot] route-after-warp failed: %s", exc)

        return AutopilotRunResult(
            tenant_id=tenant_id,
            job_id=result.job_id,
            leads_found=result.leads_found,
            sequences_queued=result.sequences_queued,
            skipped_deduped=skipped_deduped,
            paused=False,
            pause_reason="",
            emails_sent=emails_sent,
            emails_failed=emails_failed,
            campaign_id=campaign_id,
            sector_stats=sector_stats,
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    async def _source_leads(self, icp: dict) -> list[dict]:
        """Keyword ICP → Apollo company discovery → contact discovery → lead dicts.

        If icp["locations"] is a list, the search metro rotates daily so the same
        keyword keeps yielding fresh leads (dedup screens any overlap)."""
        import uuid as _uuid
        from modules.m1_intelligence.company_search import search_companies
        from modules.m1_intelligence.contact_discover import discover_contacts_batch

        limit = int(icp.get("limit", 25))
        location = icp.get("location", "")
        locations = icp.get("locations") or []
        if locations:
            from datetime import date
            location = locations[date.today().toordinal() % len(locations)]
            logger.info("[autopilot] metro rotation → %s", location)
        companies = await search_companies(
            keywords=icp.get("keywords", ""),
            location=location,
            industry=icp.get("industry", ""),
            limit=min(limit * 2, 50),  # over-fetch: not every company yields an email
        )
        if not companies:
            return []
        batch = [
            {
                "index":   i,
                "name":    c.get("name", ""),
                "domain":  c.get("domain", ""),
                "website": c.get("website", ""),
                "phone":   c.get("phone", ""),
                "yelp_id": c.get("yelp_id", ""),
            }
            for i, c in enumerate(companies)
        ]
        enriched = await discover_contacts_batch(batch, max_parallel=5)
        leads = []
        for r in enriched:
            email = (r.get("email") or "").strip()
            if not email:
                continue
            company = companies[r["index"]]
            name = f"{r.get('first_name', '')} {r.get('last_name', '')}".strip()
            leads.append({
                "lead_id": r.get("lead_id") or str(_uuid.uuid4()),
                "name":    name or company.get("name", ""),
                "email":   email,
                "title":   r.get("title", ""),
                "company": company.get("name", ""),
            })
            if len(leads) >= limit:
                break
        return leads

    def _dedup_leads(self, tenant_id: str, leads: list[dict]) -> tuple[list[dict], int]:
        """Drop leads already emailed in the trailing 90 days or unsubscribed."""
        if not leads:
            return [], 0
        from datetime import timedelta
        emails = [l["email"] for l in leads]
        blocked: set[str] = set()
        try:
            since = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
            prior = (
                _db().table("urap_campaign_sends")
                .select("to_email")
                .eq("tenant_id", tenant_id)
                .in_("to_email", emails)
                .gte("sent_at", since)
                .execute()
            )
            blocked |= {r["to_email"] for r in (prior.data or [])}
        except Exception as exc:
            logger.warning("[autopilot] send-history dedup check failed: %s", exc)
        try:
            unsubs = (
                _db().table("urap_contacts")
                .select("email")
                .eq("tenant_id", tenant_id)
                .eq("global_status", "unsubscribe")
                .in_("email", emails)
                .execute()
            )
            blocked |= {r["email"] for r in (unsubs.data or [])}
        except Exception as exc:
            logger.warning("[autopilot] unsubscribe dedup check failed: %s", exc)
        fresh = [l for l in leads if l["email"] not in blocked]
        return fresh, len(leads) - len(fresh)

    async def _send_generated(self, tenant_id: str, icp: dict, generated: list[dict]) -> tuple[int, int, str]:
        """Send warp-generated copy via the provider waterfall; record a real
        campaign row + per-send rows (urap_campaign_sends FK requires a campaign uuid)."""
        import uuid as _uuid
        from modules.m2_outreach.email_sequence import EmailSequenceService

        from_email = icp.get("from_email") or os.getenv("OUTREACH_FROM_EMAIL", "djdabblin@gmail.com")
        from_name = icp.get("from_name") or os.getenv("OUTREACH_FROM_NAME", "Dennis Day II — Dabblin Cloud")
        today = datetime.now(timezone.utc).date().isoformat()
        label = icp.get("icp_label", "ICP")

        campaign_row = {
            "id": str(_uuid.uuid4()),
            "tenant_id": tenant_id,
            "name": f"Autopilot — {label} — {today}",
            "list_id": None,
            "from_email": from_email,
            "from_name": from_name,
            "subject_template": "(autopilot: per-lead AI copy)",
            "body_template": "(autopilot: per-lead AI copy)",
            "ai_personalize": True,
            "status": "sending",
        }
        _db().table("urap_campaigns").insert(campaign_row).execute()
        campaign_id = campaign_row["id"]

        svc = EmailSequenceService()
        sent = failed = 0
        send_records: list[dict] = []
        
        for g in generated:
            email = (g.get("email") or "").strip()
            if not email:
                continue
                
            base_html = g.get("body_html") or ""
            full_html = build_outreach_html(base_html)
            
            result = await svc.send_single(
                lead_id=g.get("lead_id") or str(_uuid.uuid4()),
                to_email=email,
                to_name=g.get("name") or "",
                from_email=from_email,
                from_name=from_name,
                subject=g.get("subject") or f"Quick question for {g.get('company', 'you')}",
                body_html=full_html,
                require_consent=False,
                tag=f"campaign:{campaign_id}",
            )
            send_records.append({
                "id":          str(_uuid.uuid4()),
                "campaign_id": campaign_id,
                "tenant_id":   tenant_id,
                "lead_id":     g.get("lead_id") or "",
                "to_email":    email,
                "subject":     g.get("subject") or "",
                "body_html":   full_html,
                "status":      "sent" if result.success else "failed",
                "provider":    result.provider,
                "error":       result.error,
            })
            if result.success:
                sent += 1
            else:
                failed += 1

        try:
            if send_records:
                _db().table("urap_campaign_sends").insert(send_records).execute()
            _db().table("urap_campaigns").update({
                "status": "sent", "sent_count": sent, "failed_count": failed,
            }).eq("id", campaign_id).execute()
        except Exception as exc:
            logger.error("[autopilot] persist send records failed: %s", exc)
        return sent, failed, campaign_id

    def _get_routable_leads(self, tenant_id: str, min_score: int, limit: int) -> list[dict]:
        """Pull recently enriched contacts above min_score for route-after-warp dispatch."""
        try:
            from modules.m2_outreach.email_sequence import EmailSequenceService
            svc = EmailSequenceService()
            result = (
                _db().table("urap_contacts")
                .select("*")
                .eq("tenant_id", tenant_id)
                .is_("routed_at", "null")
                .limit(min(limit * 2, 100))
                .execute()
            )
            contacts = result.data or []
            scored = [
                {**c, "score": svc.score_intent(c)}
                for c in contacts
                if svc.score_intent(c) >= min_score
            ]
            return sorted(scored, key=lambda x: x["score"], reverse=True)[:limit]
        except Exception as exc:
            logger.warning("[autopilot] _get_routable_leads error: %s", exc)
            return []

    def _unsubscribe_rate(self, tenant_id: str) -> float:
        """Compute unsubscribe rate = unsubscribed / total leads in last 7 days."""
        try:
            from datetime import timedelta
            since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
            total = _db().table("urap_contacts").select("id", count="exact").eq("tenant_id", tenant_id).gte("created_at", since).execute()
            unsubs = _db().table("urap_contacts").select("id", count="exact").eq("tenant_id", tenant_id).eq("global_status", "unsubscribe").gte("updated_at", since).execute()
            t = getattr(total, "count", 0) or 1
            u = getattr(unsubs, "count", 0) or 0
            return u / t
        except Exception:
            return 0.0

    def _sent_today(self, tenant_id: str) -> int:
        """Count emails actually sent today by autopilot campaigns (throttle check)."""
        try:
            from datetime import date
            today = date.today().isoformat()
            result = (
                _db().table("urap_campaigns")
                .select("sent_count")
                .eq("tenant_id", tenant_id)
                .like("name", "Autopilot —%")
                .gte("created_at", today)
                .execute()
            )
            return sum(r.get("sent_count", 0) for r in (result.data or []))
        except Exception:
            return 0

    def _log_run(self, tenant_id: str, stats: dict) -> None:
        try:
            _db().table("urap_autopilot_configs").update({
                "last_run_at": datetime.now(timezone.utc).isoformat(),
                "last_run_stats": stats,
            }).eq("tenant_id", tenant_id).execute()
        except Exception as exc:
            logger.warning("[autopilot] log_run failed: %s", exc)
