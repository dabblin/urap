"""Race Agents — CPL auction: simultaneous ping to all configured marketplaces,
highest bidder wins and receives the lead dispatch (Sprint 8 / Bass.EXE pattern)."""

import asyncio
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")

DEFAULT_TIMEOUT = 5.0   # seconds to wait for each marketplace bid
PING_PAYLOAD_KEY = "ping"  # key added to payload to signal auction ping


def _db():
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_KEY)


@dataclass
class BidResult:
    marketplace_id: str
    marketplace_name: str
    cpl: float
    accepted: bool
    error: str = ""


@dataclass
class RaceResult:
    auction_id: str
    tenant_id: str
    lead_id: str
    winner_marketplace_id: str
    winner_marketplace_name: str
    winning_cpl: float
    all_bids: list = field(default_factory=list)   # list[BidResult dicts]
    dispatched: bool = False
    error: str = ""
    created_at: str = ""


class RaceAuction:
    """CPL auction engine. Pings all configured marketplaces simultaneously,
    picks the highest CPL bid that accepts the lead, then dispatches to winner."""

    async def run_auction(
        self,
        tenant_id: str,
        lead: dict,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> RaceResult:
        """Run a single-lead CPL auction across all configured marketplaces."""
        auction_id = str(uuid.uuid4())
        lead_id = str(lead.get("id", lead.get("email", auction_id[:8])))
        result = RaceResult(
            auction_id=auction_id,
            tenant_id=tenant_id,
            lead_id=lead_id,
            winner_marketplace_id="",
            winner_marketplace_name="",
            winning_cpl=0.0,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        configs = self._get_configs(tenant_id)
        if not configs:
            result.error = "No configured marketplaces for this tenant"
            self._log_result(result)
            return result

        # Simultaneous ping to all marketplaces
        tasks = [self._bid_marketplace(cfg, lead, timeout) for cfg in configs]
        bids: list[BidResult] = await asyncio.gather(*tasks, return_exceptions=False)
        result.all_bids = [
            {
                "marketplace_id": b.marketplace_id,
                "marketplace_name": b.marketplace_name,
                "cpl": b.cpl,
                "accepted": b.accepted,
                "error": b.error,
            }
            for b in bids
        ]

        # Pick highest accepting bid
        winning_bids = sorted(
            [b for b in bids if b.accepted and b.cpl > 0],
            key=lambda x: x.cpl,
            reverse=True,
        )
        if not winning_bids:
            result.error = "No marketplace accepted this lead"
            self._log_result(result)
            return result

        winner = winning_bids[0]
        result.winner_marketplace_id = winner.marketplace_id
        result.winner_marketplace_name = winner.marketplace_name
        result.winning_cpl = winner.cpl

        # Dispatch to winner
        winner_cfg = next((c for c in configs if c["marketplace_id"] == winner.marketplace_id), None)
        if winner_cfg:
            try:
                payload = self._build_payload(lead)
                headers = {"Content-Type": "application/json"}
                if winner_cfg.get("api_key"):
                    headers["Authorization"] = f"Bearer {winner_cfg['api_key']}"
                async with httpx.AsyncClient(timeout=10.0) as client:
                    await client.post(winner_cfg["webhook_url"], json=payload, headers=headers)
                result.dispatched = True
                self._mark_lead_routed(tenant_id, lead_id)
            except Exception as exc:
                result.error = f"Dispatch failed: {exc}"

        self._log_result(result)
        return result

    async def run_bulk(
        self,
        tenant_id: str,
        leads: list[dict],
        timeout: float = DEFAULT_TIMEOUT,
    ) -> list[RaceResult]:
        """Run CPL auction for each lead sequentially (avoids hammering marketplaces)."""
        results = []
        for lead in leads:
            r = await self.run_auction(tenant_id, lead, timeout)
            results.append(r)
        return results

    def get_results(self, tenant_id: str, limit: int = 20) -> dict:
        """Return recent auction results + aggregate stats."""
        try:
            rows = (
                _db().table("urap_race_results")
                .select("*")
                .eq("tenant_id", tenant_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            results = rows.data or []
            total_earned = sum(r.get("winning_cpl", 0) for r in results if r.get("dispatched"))
            total_auctions = len(results)
            won = sum(1 for r in results if r.get("dispatched"))
            return {
                "results": results,
                "total_auctions": total_auctions,
                "auctions_won": won,
                "total_earned": round(total_earned, 2),
            }
        except Exception as exc:
            logger.error("[race] get_results error: %s", exc)
            return {"results": [], "total_auctions": 0, "auctions_won": 0, "total_earned": 0.0}

    # ── Private ───────────────────────────────────────────────────────────────

    async def _bid_marketplace(
        self, marketplace: dict, lead: dict, timeout: float
    ) -> BidResult:
        """Send auction ping to one marketplace. Returns CPL from response or config fallback."""
        mp_id = marketplace.get("marketplace_id", "")
        mp_name = marketplace.get("name", mp_id)
        config_cpl = float(marketplace.get("cpl", 0.0))

        if not marketplace.get("webhook_url"):
            return BidResult(mp_id, mp_name, 0.0, False, "No webhook URL configured")

        try:
            payload = self._build_payload(lead)
            payload[PING_PAYLOAD_KEY] = True  # signal auction ping, not final post
            headers = {"Content-Type": "application/json"}
            if marketplace.get("api_key"):
                headers["Authorization"] = f"Bearer {marketplace['api_key']}"

            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(marketplace["webhook_url"], json=payload, headers=headers)

            if resp.status_code in (200, 201, 202):
                # Try to parse dynamic CPL from response body
                try:
                    data = resp.json()
                    dynamic_cpl = float(data.get("cpl") or data.get("price") or data.get("bid") or 0)
                    accepted = data.get("accepted", True)
                    final_cpl = dynamic_cpl if dynamic_cpl > 0 else config_cpl
                    return BidResult(mp_id, mp_name, final_cpl, accepted and final_cpl > 0)
                except Exception:
                    return BidResult(mp_id, mp_name, config_cpl, config_cpl > 0)
            else:
                return BidResult(mp_id, mp_name, 0.0, False, f"HTTP {resp.status_code}")
        except httpx.TimeoutException:
            return BidResult(mp_id, mp_name, 0.0, False, "Timeout")
        except Exception as exc:
            return BidResult(mp_id, mp_name, 0.0, False, str(exc)[:120])

    def _get_configs(self, tenant_id: str) -> list[dict]:
        """Pull all configured marketplace webhooks for this tenant + merge catalog names."""
        try:
            rows = (
                _db().table("urap_marketplace_configs")
                .select("*")
                .eq("tenant_id", tenant_id)
                .neq("webhook_url", "")
                .execute()
            )
            return rows.data or []
        except Exception as exc:
            logger.error("[race] _get_configs error: %s", exc)
            return []

    def _build_payload(self, lead: dict) -> dict:
        """Map URAP contact fields to standardized marketplace payload schema."""
        return {
            "first_name":     lead.get("first_name", ""),
            "last_name":      lead.get("last_name", ""),
            "business_name":  lead.get("company", lead.get("business_name", "")),
            "email":          lead.get("email", ""),
            "phone":          lead.get("phone", ""),
            "address":        lead.get("address", ""),
            "city":           lead.get("city", ""),
            "state":          lead.get("state", ""),
            "zip":            lead.get("zip", ""),
            "category":       lead.get("industry", lead.get("category", "")),
            "score":          lead.get("score", 0),
            "source":         "urap_race",
            "timestamp":      datetime.now(timezone.utc).isoformat(),
        }

    def _log_result(self, result: RaceResult) -> None:
        try:
            _db().table("urap_race_results").insert({
                "id":                      result.auction_id,
                "tenant_id":               result.tenant_id,
                "lead_id":                 result.lead_id,
                "winner_marketplace_id":   result.winner_marketplace_id,
                "winner_marketplace_name": result.winner_marketplace_name,
                "winning_cpl":             result.winning_cpl,
                "all_bids":                result.all_bids,
                "dispatched":              result.dispatched,
                "error":                   result.error,
                "created_at":              result.created_at or datetime.now(timezone.utc).isoformat(),
            }).execute()
        except Exception as exc:
            logger.warning("[race] _log_result error: %s", exc)

    def _mark_lead_routed(self, tenant_id: str, lead_id: str) -> None:
        try:
            _db().table("urap_contacts").update({
                "routed_at": datetime.now(timezone.utc).isoformat(),
            }).eq("tenant_id", tenant_id).eq("id", lead_id).execute()
        except Exception:
            pass
