"""Module I — Global Intelligence & Data Enrichment waterfall orchestrator.

Waterfall:  Prospeo (primary) → Snov.io (fallback) → Hunter.io (domain sweep)
Gate:       Cleanlist.ai runs on every result before Supabase cache write.
Cache:      urap_contacts table — upsert on email, 30-day enrichment freshness.
"""
import os
import uuid
import sys
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from tier3.prospeo.client import ProspeoClient
from tier3.snov.client import SnovClient
from tier3.cleanlist.client import CleanlistClient
from tier3.hunter.client import HunterClient


def _build_contact(
    *,
    tenant_id: str,
    first_name: Optional[str],
    last_name: Optional[str],
    email: str,
    domain: str,
    title: Optional[str],
    verified: bool,
    source: str,
) -> dict:
    name = f"{first_name or ''} {last_name or ''}".strip() or email.split("@")[0]
    return {
        "lead_id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "name": name,
        "email": email,
        "company": domain,
        "title": title or "",
        "email_verified": verified,
        "enrichment_source": source,
        "global_status": "prospecting",
        "channel_state": {"email": "idle", "sms": "idle", "linkedin": "idle", "voice": "idle"},
        "intent_signals": [],
    }


class EnrichmentService:
    def __init__(self) -> None:
        self.prospeo = ProspeoClient()
        self.snov = SnovClient()
        self.cleanlist = CleanlistClient()
        self.hunter = HunterClient()
        self._supabase = None

    def _db(self):
        if self._supabase is None:
            from supabase import create_client
            url = os.environ["SUPABASE_URL"]
            key = os.environ["SUPABASE_ANON_KEY"]
            self._supabase = create_client(url, key)
        return self._supabase

    async def _quality_gate(self, email: str, already_verified: bool) -> bool:
        """Return True if email passes Cleanlist gate. Skips if already Prospeo-verified."""
        if already_verified:
            return True
        try:
            result = await self.cleanlist.verify_email(email)
            if result is None:
                return True  # gate unavailable — allow through
            if result.is_spam_trap or result.is_disposable:
                return False
            return result.is_valid
        except Exception:
            return True  # gate failure is non-fatal

    def _cache(self, contact: dict) -> None:
        try:
            self._db().table("urap_contacts").upsert(contact, on_conflict="email").execute()
        except Exception:
            pass  # cache miss is non-fatal

    def _cache_many(self, contacts: list[dict]) -> None:
        """Batch upsert. Only rows with an email are persisted (email is the conflict key)."""
        rows = [c for c in contacts if c.get("email")]
        if not rows:
            return
        # Strip fields the urap_contacts cache doesn't carry to avoid schema errors.
        clean = [{k: v for k, v in r.items() if k != "location"} for r in rows]
        try:
            self._db().table("urap_contacts").upsert(clean, on_conflict="email").execute()
        except Exception:
            pass  # cache miss is non-fatal

    async def enrich_contact(
        self,
        tenant_id: str,
        first_name: Optional[str],
        last_name: Optional[str],
        domain: str,
        title: Optional[str] = None,
    ) -> Optional[dict]:
        """Single-contact enrichment. Returns None if no email found or quality gate rejects."""
        email: Optional[str] = None
        verified = False
        source = ""
        result_first = first_name
        result_last = last_name

        # Layer 1 — Prospeo
        if first_name and last_name:
            try:
                p = await self.prospeo.find_email(first_name, last_name, domain)
                if p:
                    email, verified, source = p.email, p.verified, "prospeo"
                    result_first = p.first_name or first_name
                    result_last = p.last_name or last_name
            except Exception:
                pass

        # Layer 2 — Snov.io
        if not email and first_name and last_name:
            try:
                s = await self.snov.find_email(first_name, last_name, domain)
                if s:
                    email, verified, source = s.email, s.verified, "snov"
            except Exception:
                pass

        # Layer 3 — Hunter (domain sweep — no name required)
        if not email:
            try:
                hits = await self.hunter.domain_search(domain, limit=3)
                if hits:
                    h = hits[0]
                    email, source = h.email, "hunter"
                    verified = h.confidence > 70
                    result_first = h.first_name or first_name
                    result_last = h.last_name or last_name
                    title = h.title or title
            except Exception:
                pass

        if not email:
            return None

        if not await self._quality_gate(email, verified):
            return None

        contact = _build_contact(
            tenant_id=tenant_id,
            first_name=result_first,
            last_name=result_last,
            email=email,
            domain=domain,
            title=title,
            verified=verified,
            source=source,
        )
        self._cache(contact)
        return contact

    async def bulk_enrich_domain(
        self, tenant_id: str, domain: str, limit: int = 25
    ) -> list[dict]:
        """Pull all known contacts at a domain via Prospeo domain search (Hunter fallback)."""
        raw_results = []

        try:
            hits = await self.prospeo.domain_search(domain, limit=limit)
            for h in hits:
                raw_results.append((h.email, h.first_name, h.last_name, None, h.verified, "prospeo"))
        except Exception:
            pass

        if not raw_results:
            try:
                hits = await self.hunter.domain_search(domain, limit=limit)
                for h in hits:
                    raw_results.append((h.email, h.first_name, h.last_name, h.title, h.confidence > 70, "hunter"))
            except Exception:
                pass

        contacts = []
        for email, fn, ln, title_val, verified, source in raw_results:
            if not await self._quality_gate(email, verified):
                continue
            c = _build_contact(
                tenant_id=tenant_id,
                first_name=fn,
                last_name=ln,
                email=email,
                domain=domain,
                title=title_val,
                verified=verified,
                source=source,
            )
            contacts.append(c)

        if contacts:
            try:
                self._db().table("urap_contacts").upsert(contacts, on_conflict="email").execute()
            except Exception:
                pass

        return contacts
