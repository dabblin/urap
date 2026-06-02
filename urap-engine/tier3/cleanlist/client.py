"""Cleanlist.ai email verification client — quality gate (all waterfall results pass through).

Free tier: 30 verifications/month, permanent free plan.
Docs: https://cleanlist.ai/api-documentation
Rejects spam traps and disposable addresses before Supabase cache write.
"""
import os
import httpx
from typing import Optional
from dataclasses import dataclass


CLEANLIST_BASE = "https://api.cleanlist.ai"


@dataclass
class CleanlistResult:
    email: str
    is_valid: bool
    is_catch_all: bool
    is_spam_trap: bool
    is_disposable: bool
    score: int  # 0–100, higher = safer to send
    raw: dict


class CleanlistClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("CLEANLIST_API_KEY", "")

    def _is_configured(self) -> bool:
        return bool(self.api_key)

    async def verify_email(self, email: str) -> Optional[CleanlistResult]:
        if not self._is_configured():
            return None
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{CLEANLIST_BASE}/v1/verify",
                headers={"X-Api-Key": self.api_key, "Content-Type": "application/json"},
                json={"email": email},
            )
        if resp.status_code != 200:
            return None
        data = resp.json()
        result = data.get("result", "")
        return CleanlistResult(
            email=email,
            is_valid=result == "valid",
            is_catch_all=data.get("is_catch_all", False),
            is_spam_trap=data.get("is_spam_trap", False),
            is_disposable=data.get("is_disposable", False),
            score=data.get("score", 0),
            raw=data,
        )
