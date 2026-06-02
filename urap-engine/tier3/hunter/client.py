"""Hunter.io email enrichment client — domain sweep layer (waterfall layer 3 / bulk fallback).

Free tier: 50 requests/month, no CC required.
API docs: https://hunter.io/api-documentation/v2
Best for: pulling all known contacts at a company domain.
"""
import os
import httpx
from typing import Optional
from dataclasses import dataclass, field


HUNTER_BASE = "https://api.hunter.io/v2"


@dataclass
class HunterResult:
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    title: Optional[str]
    department: Optional[str]
    confidence: int  # 0–100
    company_domain: str
    raw: dict = field(default_factory=dict)


class HunterClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("HUNTER_API_KEY", "")

    def _is_configured(self) -> bool:
        return bool(self.api_key)

    async def find_email(
        self, first_name: str, last_name: str, domain: str
    ) -> Optional[HunterResult]:
        if not self._is_configured():
            return None
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{HUNTER_BASE}/email-finder",
                params={
                    "domain": domain,
                    "first_name": first_name,
                    "last_name": last_name,
                    "api_key": self.api_key,
                },
            )
        if resp.status_code != 200:
            return None
        data = resp.json().get("data", {})
        email = data.get("email")
        if not email:
            return None
        return HunterResult(
            email=email,
            first_name=data.get("first_name") or first_name,
            last_name=data.get("last_name") or last_name,
            title=data.get("position"),
            department=None,
            confidence=data.get("confidence", 0),
            company_domain=domain,
            raw=data,
        )

    async def domain_search(self, domain: str, limit: int = 10) -> list[HunterResult]:
        """Pull all publicly known emails at a domain."""
        if not self._is_configured():
            return []
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{HUNTER_BASE}/domain-search",
                params={"domain": domain, "limit": limit, "api_key": self.api_key},
            )
        if resp.status_code != 200:
            return []
        results = []
        for entry in resp.json().get("data", {}).get("emails", []):
            email = entry.get("value")
            if not email:
                continue
            results.append(HunterResult(
                email=email,
                first_name=entry.get("first_name"),
                last_name=entry.get("last_name"),
                title=entry.get("position"),
                department=entry.get("department"),
                confidence=entry.get("confidence", 0),
                company_domain=domain,
                raw=entry,
            ))
        return results
