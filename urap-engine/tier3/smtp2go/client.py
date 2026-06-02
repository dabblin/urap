"""SMTP2GO email sender — primary outreach provider.

Free tier: 1,000 emails/month. No CC required.
Full SPF/DKIM/DMARC support. Built-in domain warm-up scheduler.
Signup: https://www.smtp2go.com/

API: POST https://api.smtp2go.com/v3/email/send
Env: SMTP2GO_API_KEY
"""
import os
import httpx
from dataclasses import dataclass
from typing import Optional


SMTP2GO_API = "https://api.smtp2go.com/v3/email/send"


@dataclass
class SendResult:
    success: bool
    provider: str = "smtp2go"
    message_id: Optional[str] = None
    error: Optional[str] = None


class SMTP2GOClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("SMTP2GO_API_KEY", "")

    def _is_configured(self) -> bool:
        return bool(self.api_key)

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
            return SendResult(success=False, error="SMTP2GO_NOT_CONFIGURED")
        payload = {
            "api_key": self.api_key,
            "to": [f"{to_name} <{to_email}>"],
            "sender": f"{from_name} <{from_email}>",
            "subject": subject,
            "html_body": body_html,
        }
        if reply_to:
            payload["custom_headers"] = [{"header": "Reply-To", "value": reply_to}]
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(SMTP2GO_API, json=payload)
            data = resp.json()
            if resp.status_code == 200 and data.get("data", {}).get("succeeded") == 1:
                msg_id = (data.get("data") or {}).get("email_id", "")
                return SendResult(success=True, message_id=msg_id)
            return SendResult(success=False, error=str(data.get("data", {}).get("failures", resp.text)))
        except Exception as exc:
            return SendResult(success=False, error=str(exc))
