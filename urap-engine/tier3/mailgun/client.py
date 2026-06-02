"""Mailgun email sender — burst fallback provider.

Free tier: 3,000 emails/month (first 3 months), then Flex pay-as-you-go.
Developer API, good for webhook-driven sends.
Signup: https://signup.mailgun.com/

API: POST https://api.mailgun.net/v3/{domain}/messages
Env: MAILGUN_API_KEY, MAILGUN_DOMAIN
"""
import os
import httpx
from dataclasses import dataclass
from typing import Optional


@dataclass
class SendResult:
    success: bool
    provider: str = "mailgun"
    message_id: Optional[str] = None
    error: Optional[str] = None


class MailgunClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("MAILGUN_API_KEY", "")
        self.domain = os.getenv("MAILGUN_DOMAIN", "")

    def _is_configured(self) -> bool:
        return bool(self.api_key and self.domain)

    def _api_url(self) -> str:
        return f"https://api.mailgun.net/v3/{self.domain}/messages"

    async def send(
        self,
        *,
        to_email: str,
        to_name: str,
        from_email: str,
        from_name: str,
        subject: str,
        body_html: str,
        reply_to: Optional[str] = None,
    ) -> SendResult:
        if not self._is_configured():
            return SendResult(success=False, error="MAILGUN_NOT_CONFIGURED")
        data = {
            "from": f"{from_name} <{from_email}>",
            "to": f"{to_name} <{to_email}>",
            "subject": subject,
            "html": body_html,
        }
        if reply_to:
            data["h:Reply-To"] = reply_to
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    self._api_url(),
                    data=data,
                    auth=("api", self.api_key),
                )
            if resp.status_code == 200:
                return SendResult(success=True, message_id=resp.json().get("id", "").strip("<>"))
            return SendResult(success=False, error=resp.text)
        except Exception as exc:
            return SendResult(success=False, error=str(exc))
