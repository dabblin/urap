"""Brevo (formerly Sendinblue) email sender — overflow provider.

Free tier: ~9,000 emails/month (300/day). No CC required.
Supports transactional + drip. Full SPF/DKIM/DMARC.
Signup: https://www.brevo.com/

API: POST https://api.brevo.com/v3/smtp/email
Env: BREVO_API_KEY
"""
import os
import httpx
from dataclasses import dataclass
from typing import Optional


BREVO_API = "https://api.brevo.com/v3/smtp/email"


@dataclass
class SendResult:
    success: bool
    provider: str = "brevo"
    message_id: Optional[str] = None
    error: Optional[str] = None


class BrevoClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("BREVO_API_KEY", "")

    def _is_configured(self) -> bool:
        return bool(self.api_key)

    async def send(
        self,
        *,
        to_email:  str,
        to_name:   str,
        from_email: str,
        from_name:  str,
        subject:   str,
        body_html: str,
        reply_to:  Optional[str] = None,
        tag:       Optional[str] = None,
    ) -> SendResult:
        if not self._is_configured():
            return SendResult(success=False, error="BREVO_NOT_CONFIGURED")
        payload = {
            "sender": {"name": from_name, "email": from_email},
            "to": [{"email": to_email, "name": to_name}],
            "subject": subject,
            "htmlContent": body_html,
        }
        if reply_to:
            payload["replyTo"] = {"email": reply_to}
        if tag:
            payload["tags"] = [tag]
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    BREVO_API,
                    json=payload,
                    headers={"api-key": self.api_key, "Content-Type": "application/json"},
                )
            if resp.status_code == 201:
                return SendResult(success=True, message_id=resp.json().get("messageId"))
            return SendResult(success=False, error=resp.text)
        except Exception as exc:
            return SendResult(success=False, error=str(exc))
