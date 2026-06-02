"""Autopilot runner — cron-triggered Warp Mode scheduler (Sprint 6 full implementation)."""
import os
import logging
from datetime import datetime, timezone
from dataclasses import dataclass

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")

UNSUBSCRIBE_PAUSE_THRESHOLD = 0.05   # auto-pause if >5% unsubscribe rate in last run
DEFAULT_DAILY_SEND_LIMIT    = 50


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
        """Return autopilot config for a tenant."""
        try:
            result = (
                _db().table("urap_autopilot_configs")
                .select("*")
                .eq("tenant_id", tenant_id)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as exc:
            logger.error("[autopilot] get_config error: %s", exc)
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

        icp["limit"] = min(icp.get("limit", 25), remaining)

        # Run Warp Mode
        try:
            from modules.m3_agents.warp_mode import WarpModeAgent
            warp = WarpModeAgent()
            result = await warp.run_job(icp=icp, tenant_id=tenant_id, dedup=True)
        except Exception as exc:
            logger.error("[autopilot] warp run error: %s", exc)
            return AutopilotRunResult(
                tenant_id=tenant_id, job_id="", leads_found=0,
                sequences_queued=0, skipped_deduped=0,
                paused=False, pause_reason="", error=str(exc),
            )

        run_stats = {
            "leads_found": result.leads_found,
            "sequences_queued": result.sequences_queued,
            "skipped_deduped": getattr(result, "skipped_deduped", 0),
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
            skipped_deduped=getattr(result, "skipped_deduped", 0),
            paused=False,
            pause_reason="",
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

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
        """Count sequences queued today for throttle check."""
        try:
            from datetime import date
            today = date.today().isoformat()
            result = (
                _db().table("urap_warp_jobs")
                .select("sequences_queued")
                .eq("tenant_id", tenant_id)
                .gte("created_at", today)
                .execute()
            )
            return sum(r.get("sequences_queued", 0) for r in (result.data or []))
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
