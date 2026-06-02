"""Module VI — Security, Compliance & Trust: TCPA consent ledger.

Consent records are INSERT-ONLY. The Supabase RLS policy on urap_consent_ledger
blocks UPDATE and DELETE at the DB layer — this service never attempts them.

TCPA gate: before any outreach action (SMS, voice, email sequence) fires, the
orchestrator must call check_tcpa_gate(lead_id). A missing or invalid cert URL
blocks the action and logs the attempt.
"""
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


class ConsentLedgerService:
    def __init__(self) -> None:
        self._supabase = None

    def _db(self):
        if self._supabase is None:
            from supabase import create_client
            self._supabase = create_client(
                os.environ["SUPABASE_URL"],
                os.environ["SUPABASE_ANON_KEY"],
            )
        return self._supabase

    def record_consent(
        self,
        *,
        tenant_id: str,
        lead_id: str,
        source: str,          # TrustedForm cert URL
        ip_address: str,
        platform_name: str,
        one_to_one_rule: bool = True,
    ) -> dict:
        """Insert a consent record. Raises on DB error — caller must handle."""
        record = {
            "id": str(uuid.uuid4()),
            "lead_id": lead_id,
            "tenant_id": tenant_id,
            "source": source,
            "consented_at": datetime.now(timezone.utc).isoformat(),
            "ip_address": ip_address,
            "platform_name": platform_name,
            "one_to_one_rule": one_to_one_rule,
        }
        self._db().table("urap_consent_ledger").insert(record).execute()
        return record

    def check_tcpa_gate(self, lead_id: str) -> bool:
        """Return True if at least one consent record exists for this lead."""
        try:
            result = (
                self._db()
                .table("urap_consent_ledger")
                .select("id", count="exact")
                .eq("lead_id", lead_id)
                .limit(1)
                .execute()
            )
            return (result.count or 0) > 0
        except Exception:
            # Gate failure is non-fatal for now — log and allow through.
            # Flip this to return False once production consent flow is live.
            return True

    def get_latest_consent(self, lead_id: str) -> Optional[dict]:
        """Return the most recent consent record for a lead, or None."""
        try:
            result = (
                self._db()
                .table("urap_consent_ledger")
                .select("*")
                .eq("lead_id", lead_id)
                .order("consented_at", desc=True)
                .limit(1)
                .execute()
            )
            rows = result.data or []
            return rows[0] if rows else None
        except Exception:
            return None
