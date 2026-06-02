"""Snov.io email enrichment client — waterfall fallback layer 2.

Free tier: 50 credits/month, no CC required.
API docs: https://snov.io/api
Auth: OAuth2 client_credentials flow.
"""
import os
import httpx
from typing import Optional
from dataclasses import dataclass, field


SNOV_BASE = "https://api.snov.io/v1"


@dataclass
class SnovResult:
    email: str
    verified: bool
    first_name: Optional[str]
    last_name: Optional[str]
    title: Optional[str]
    company: str
    raw: dict = field(default_factory=dict)


class SnovClient:
    def __init__(self) -> None:
        self.client_id = os.getenv("SNOV_CLIENT_ID", "")
        self.client_secret = os.getenv("SNOV_CLIENT_SECRET", "")
        self._token: Optional[str] = None

    def _is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

    async def _get_token(self) -> str:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{SNOV_BASE}/oauth/access_token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
            )
            resp.raise_for_status()
        self._token = resp.json()["access_token"]
        return self._token

    async def find_email(
        self, first_name: str, last_name: str, domain: str
    ) -> Optional[SnovResult]:
        if not self._is_configured():
            return None
        token = await self._get_token()
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{SNOV_BASE}/get-emails-from-url",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "sessionToken": token,
                    "first_name": first_name,
                    "last_name": last_name,
                    "url": f"https://{domain}",
                },
            )
        if resp.status_code != 200:
            return None
        data = resp.json()
        if not data.get("success"):
            return None
        emails = data.get("emails", [])
        if not emails:
            return None
        top = emails[0]
        email = top.get("email")
        if not email:
            return None
        return SnovResult(
            email=email,
            verified=top.get("status") == "valid",
            first_name=first_name,
            last_name=last_name,
            title=None,
            company=domain,
            raw=top,
        )
