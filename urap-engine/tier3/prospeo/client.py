"""Prospeo email enrichment client — primary waterfall layer.

Free tier: 75 verified emails/month, no CC required.
API docs: https://prospeo.io/api-docs
"""
import os
import httpx
from typing import Optional
from dataclasses import dataclass, field


PROSPEO_BASE = "https://api.prospeo.io"


@dataclass
class ProspeoResult:
    email: str
    verified: bool
    confidence: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    title: Optional[str]
    company_domain: str
    linkedin_url: Optional[str] = None
    raw: dict = field(default_factory=dict)


class ProspeoClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("PROSPEO_API_KEY", "")

    @property
    def _headers(self) -> dict:
        return {"X-KEY": self.api_key, "Content-Type": "application/json"}

    def _is_configured(self) -> bool:
        return bool(self.api_key)

    def _parse_person(self, person: dict, domain: str) -> Optional["ProspeoResult"]:
        """Parse a person object from either enrich-person or search-person response."""
        email = person.get("email") or (person.get("email_data") or {}).get("email")
        if not email:
            return None
        verified_raw = (person.get("email_data") or {}).get("verification_status") or person.get("verification_status")
        verified = str(verified_raw).upper() in ("VALID", "VERIFIED")
        return ProspeoResult(
            email=email,
            verified=verified,
            confidence=person.get("confidence"),
            first_name=person.get("first_name"),
            last_name=person.get("last_name"),
            title=person.get("job_title") or person.get("title"),
            company_domain=domain,
            linkedin_url=person.get("linkedin_url"),
            raw=person,
        )

    async def find_email(
        self, first_name: str, last_name: str, domain: str
    ) -> Optional["ProspeoResult"]:
        if not self._is_configured():
            return None
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{PROSPEO_BASE}/enrich-person",
                headers=self._headers,
                json={
                    "data": {
                        "first_name": first_name,
                        "last_name": last_name,
                        "company_website": domain,
                    },
                    "only_verified_email": False,
                },
            )
        if resp.status_code != 200:
            return None
        data = resp.json()
        person = data.get("person") or data.get("data") or data
        if isinstance(person, dict) and person.get("error"):
            return None
        return self._parse_person(person, domain)

    async def domain_search(self, domain: str, limit: int = 10) -> list["ProspeoResult"]:
        """Pull contacts at a domain via search-person + enrich in one pass."""
        if not self._is_configured():
            return []
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                f"{PROSPEO_BASE}/search-person",
                headers=self._headers,
                json={
                    "filters": {
                        # Prospeo expects a list value here, not {"value": ...}
                        "company_website": [domain],
                    },
                    "page": 1,
                },
            )
        if resp.status_code != 200:
            return []
        data = resp.json()
        persons = data.get("persons") or data.get("results") or data.get("data") or []
        if not isinstance(persons, list):
            return []
        results = []
        for p in persons[:limit]:
            parsed = self._parse_person(p, domain)
            if parsed:
                results.append(parsed)
        return results
