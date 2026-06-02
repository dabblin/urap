"""Module IV — Marketplace Webhook Router (Phase 1 Route Core, BizReach integration)."""
import os
import uuid
import logging
import httpx
from dataclasses import dataclass
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")

# Sample payload for webhook test — no real PII
SAMPLE_LEAD = {
    "first_name": "Alex",
    "last_name": "Sample",
    "business_name": "Sample Business LLC",
    "email": "test@sample-lead.urap.io",
    "phone": "555-000-0000",
    "address": "123 Test St",
    "city": "Atlanta",
    "state": "GA",
    "zip": "30301",
    "category": "HVAC",
    "score": 75,
    "source": "URAP",
    "timestamp": "2026-06-02T00:00:00Z",
}

# 18 pre-loaded buyer marketplaces (BizReach Route Tab R&D, 2026-06-02)
MARKETPLACE_CATALOG: list[dict] = [
    {"id": "px",          "name": "PX Marketplace",        "cpl_range": "$30–$150",  "best_for": "Real-time Ping/Post bidding, all verticals"},
    {"id": "leadsmarket", "name": "LeadsMarket",            "cpl_range": "$25–$260",  "best_for": "Finance & lending, AI-powered routing"},
    {"id": "leadpoint",   "name": "LeadPoint",              "cpl_range": "$20–$100",  "best_for": "World's largest leads exchange"},
    {"id": "leadexec",    "name": "LeadExec / ClickPoint",  "cpl_range": "$40–$120",  "best_for": "Enterprise XML + Ping/Post distribution"},
    {"id": "leadcrowd",   "name": "LeadCrowd",              "cpl_range": "$30–$120",  "best_for": "Mortgage & financial advisors"},
    {"id": "referr",      "name": "Referr",                 "cpl_range": "$20–$90",   "best_for": "900+ categories, full transparency"},
    {"id": "leadninja",   "name": "LeadNinja",              "cpl_range": "$25–$60",   "best_for": "Individual reps & small teams"},
    {"id": "oversource",  "name": "Oversource",             "cpl_range": "$30–$80",   "best_for": "Pay-later and pay-% of profit"},
    {"id": "elitelead",   "name": "Elite Lead Exchange",    "cpl_range": "$20–$50",   "best_for": "Free & transparent exchange platform"},
    {"id": "salespread",  "name": "SaleSpread",             "cpl_range": "$15–$40",   "best_for": "Quick sales for low-priority leads"},
    {"id": "leadfellow",  "name": "Leadfellow",             "cpl_range": "$25–$65",   "best_for": "B2B partner network, trusted circles"},
    {"id": "leadswap",    "name": "LeadSwap",               "cpl_range": "$25–$55",   "best_for": "Upload verified lists, keep 76%"},
    {"id": "cloudtask",   "name": "CloudTask Marketplace",  "cpl_range": "$40–$80",   "best_for": "Sales outsourcing & remote agencies"},
    {"id": "eprospects",  "name": "E-Prospects.biz",        "cpl_range": "$20–$50",   "best_for": "eBay-style lead marketplace"},
    {"id": "gotradelead", "name": "GoTradeLeads",           "cpl_range": "$10–$30",   "best_for": "Free B2B trade leads, global buyers"},
    {"id": "serchz",      "name": "Serchz",                 "cpl_range": "$30–$70",   "best_for": "B2B lead gen SaaS infrastructure"},
    {"id": "premierbiz",  "name": "Premier Business Club",  "cpl_range": "$15–$35",   "best_for": "Regional/language-sorted trade leads"},
    {"id": "custom",      "name": "Custom / Agency",        "cpl_range": "$150+",     "best_for": "Your own buyers — premium direct webhook"},
]


def _db():
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_KEY)


@dataclass
class DispatchResult:
    session_id: str
    marketplace_id: str
    marketplace_name: str
    leads_routed: int
    estimated_earnings: float
    failed: int
    error: str = ""


class MarketplaceRouter:
    """Routes enriched URAP contacts to external buyer marketplace webhooks."""

    def get_catalog(self) -> list[dict]:
        return MARKETPLACE_CATALOG

    def get_marketplace_configs(self, tenant_id: str) -> list[dict]:
        """Return per-tenant marketplace configs merged with catalog metadata."""
        try:
            result = (
                _db().table("urap_marketplace_configs")
                .select("*")
                .eq("tenant_id", tenant_id)
                .execute()
            )
            configs_by_id = {row["marketplace_id"]: row for row in (result.data or [])}
        except Exception as exc:
            logger.warning("[marketplace_router] config fetch error: %s", exc)
            configs_by_id = {}

        merged = []
        for mp in MARKETPLACE_CATALOG:
            cfg = configs_by_id.get(mp["id"], {})
            merged.append({
                **mp,
                "webhook_url": cfg.get("webhook_url", ""),
                "api_key": cfg.get("api_key", ""),
                "cpl": cfg.get("cpl", 0.0),
                "configured": bool(cfg.get("webhook_url")),
            })
        return merged

    def save_marketplace_config(
        self,
        tenant_id: str,
        marketplace_id: str,
        webhook_url: str,
        api_key: str = "",
        cpl: float = 0.0,
    ) -> dict:
        """Upsert marketplace webhook config for a tenant."""
        try:
            now = datetime.now(timezone.utc).isoformat()
            existing = (
                _db().table("urap_marketplace_configs")
                .select("id")
                .eq("tenant_id", tenant_id)
                .eq("marketplace_id", marketplace_id)
                .limit(1)
                .execute()
            )
            row: dict = {
                "tenant_id": tenant_id,
                "marketplace_id": marketplace_id,
                "webhook_url": webhook_url.strip(),
                "api_key": api_key.strip(),
                "cpl": cpl,
                "updated_at": now,
            }
            if existing.data:
                _db().table("urap_marketplace_configs").update(row).eq(
                    "tenant_id", tenant_id
                ).eq("marketplace_id", marketplace_id).execute()
            else:
                row["id"] = str(uuid.uuid4())
                row["created_at"] = now
                _db().table("urap_marketplace_configs").insert(row).execute()
            return {"success": True, "marketplace_id": marketplace_id}
        except Exception as exc:
            logger.error("[marketplace_router] save_config error: %s", exc)
            return {"success": False, "error": str(exc)}

    async def test_webhook(self, webhook_url: str, api_key: str = "") -> dict:
        """Send a sample payload to the webhook and verify a 2xx response."""
        if not webhook_url.strip():
            return {"success": False, "status_code": 0, "error": "No webhook URL provided"}
        req_headers = {"Content-Type": "application/json"}
        if api_key:
            req_headers["Authorization"] = f"Bearer {api_key}"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(webhook_url.strip(), json=SAMPLE_LEAD, headers=req_headers)
            success = 200 <= resp.status_code < 300
            return {
                "success": success,
                "status_code": resp.status_code,
                "error": "" if success else f"HTTP {resp.status_code}",
            }
        except httpx.TimeoutException:
            return {"success": False, "status_code": 0, "error": "Timeout — webhook did not respond in 10s"}
        except Exception as exc:
            return {"success": False, "status_code": 0, "error": str(exc)}

    async def dispatch(
        self,
        tenant_id: str,
        marketplace_id: str,
        leads: list[dict],
        ping_post: bool = False,
    ) -> DispatchResult:
        """
        Route selected leads to a configured marketplace webhook.
        ping_post=True sends to ALL configured marketplaces simultaneously.
        """
        configs = self.get_marketplace_configs(tenant_id)

        if ping_post:
            targets = [c for c in configs if c.get("configured")]
        else:
            targets = [c for c in configs if c["id"] == marketplace_id and c.get("configured")]

        if not targets:
            return DispatchResult(
                session_id="", marketplace_id=marketplace_id,
                marketplace_name=marketplace_id, leads_routed=0,
                estimated_earnings=0.0, failed=0,
                error="No configured marketplace found. Add a webhook URL in Integrations → Marketplaces.",
            )

        target = targets[0]
        session_id = str(uuid.uuid4())
        routed = 0
        failed = 0

        req_headers = {"Content-Type": "application/json"}
        if target.get("api_key"):
            req_headers["Authorization"] = f"Bearer {target['api_key']}"

        async with httpx.AsyncClient(timeout=15) as client:
            for lead in leads:
                payload = self._build_payload(lead)
                try:
                    resp = await client.post(target["webhook_url"], json=payload, headers=req_headers)
                    if 200 <= resp.status_code < 300:
                        routed += 1
                    else:
                        failed += 1
                        logger.warning("[marketplace_router] dispatch %s → HTTP %s", target["id"], resp.status_code)
                except Exception as exc:
                    failed += 1
                    logger.error("[marketplace_router] dispatch error: %s", exc)

        estimated_earnings = routed * float(target.get("cpl") or 0.0)
        self._log_session(
            session_id=session_id,
            tenant_id=tenant_id,
            marketplace_id=target["id"],
            marketplace_name=target["name"],
            leads_routed=routed,
            estimated_earnings=estimated_earnings,
            failed=failed,
        )

        if routed > 0:
            self._mark_leads_routed(
                tenant_id,
                [lead.get("lead_id") or lead.get("id", "") for lead in leads[:routed]],
            )

        return DispatchResult(
            session_id=session_id,
            marketplace_id=target["id"],
            marketplace_name=target["name"],
            leads_routed=routed,
            estimated_earnings=estimated_earnings,
            failed=failed,
        )

    def get_sessions(self, tenant_id: str, limit: int = 20) -> list[dict]:
        """Return recent routing sessions for a tenant."""
        try:
            result = (
                _db().table("urap_routing_sessions")
                .select("*")
                .eq("tenant_id", tenant_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data or []
        except Exception as exc:
            logger.error("[marketplace_router] get_sessions error: %s", exc)
            return []

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _build_payload(self, lead: dict) -> dict:
        """Map URAP contact fields to the standardized marketplace payload schema."""
        name_parts = (lead.get("name") or "").split(" ", 1)
        return {
            "first_name":    lead.get("first_name") or (name_parts[0] if name_parts else ""),
            "last_name":     lead.get("last_name")  or (name_parts[1] if len(name_parts) > 1 else ""),
            "business_name": lead.get("company") or lead.get("business_name") or "",
            "email":         lead.get("email") or "",
            "phone":         lead.get("phone") or "",
            "address":       lead.get("address") or "",
            "city":          lead.get("city") or lead.get("location") or "",
            "state":         lead.get("state") or "",
            "zip":           lead.get("zip") or "",
            "category":      lead.get("category") or lead.get("industry") or "",
            "score":         int(lead.get("score") or 0),
            "source":        "URAP",
            "timestamp":     datetime.now(timezone.utc).isoformat(),
        }

    def _log_session(
        self,
        session_id: str,
        tenant_id: str,
        marketplace_id: str,
        marketplace_name: str,
        leads_routed: int,
        estimated_earnings: float,
        failed: int,
    ) -> None:
        try:
            _db().table("urap_routing_sessions").insert({
                "id":                  session_id,
                "tenant_id":           tenant_id,
                "marketplace_id":      marketplace_id,
                "marketplace_name":    marketplace_name,
                "leads_routed":        leads_routed,
                "estimated_earnings":  estimated_earnings,
                "failed":              failed,
                "created_at":          datetime.now(timezone.utc).isoformat(),
            }).execute()
        except Exception as exc:
            logger.warning("[marketplace_router] log_session error: %s", exc)

    def _mark_leads_routed(self, tenant_id: str, lead_ids: list[str]) -> None:
        now = datetime.now(timezone.utc).isoformat()
        for lead_id in lead_ids:
            if not lead_id:
                continue
            try:
                _db().table("urap_lead_distribution").update({
                    "status": "routed",
                    "routed_at": now,
                }).eq("id", lead_id).eq("tenant_id", tenant_id).execute()
            except Exception:
                pass
