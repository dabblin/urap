"""Module II — Email sequence orchestrator.

Send waterfall: SMTP2GO (primary) → Brevo (overflow) → Mailgun (burst fallback).
Before any send: TCPA gate check + channel state check.
After send: update channel state machine.
"""
import os
import sys
import uuid
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from tier3.smtp2go.client import SMTP2GOClient
from tier3.brevo.client import BrevoClient
from tier3.mailgun.client import MailgunClient
from modules.m2_outreach.channel_state_machine import ChannelStateMachine
from modules.m6_compliance.consent_ledger import ConsentLedgerService


@dataclass
class SequenceStep:
    step_number: int
    subject: str
    body_html: str
    delay_hours: int = 24


@dataclass
class EmailSequence:
    sequence_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Default Sequence"
    from_email: str = ""
    from_name: str = ""
    steps: list = field(default_factory=list)


@dataclass
class SendResult:
    success: bool
    provider: str
    message_id: Optional[str] = None
    error: Optional[str] = None


class EmailSequenceService:
    def __init__(self) -> None:
        self.smtp2go = SMTP2GOClient()
        self.brevo = BrevoClient()
        self.mailgun = MailgunClient()
        self.csm = ChannelStateMachine()
        self.consent = ConsentLedgerService()

    async def send_single(
        self,
        *,
        lead_id: str,
        to_email: str,
        to_name: str,
        from_email: str,
        from_name: str,
        subject: str,
        body_html: str,
        require_consent: bool = False,
        tag: Optional[str] = None,
    ) -> SendResult:
        """Send one email through the provider waterfall.
        TCPA gate only blocks if require_consent=True (SMS/voice default; email is opt-in-light).
        """
        if require_consent and not self.consent.check_tcpa_gate(lead_id):
            return SendResult(success=False, provider="none", error="TCPA_GATE_BLOCKED")

        if not self.csm.can_send(lead_id, "email"):
            return SendResult(success=False, provider="none", error="CHANNEL_STATE_BLOCKED")

        result = await self.smtp2go.send(
            to_email=to_email, to_name=to_name,
            from_email=from_email, from_name=from_name,
            subject=subject, body_html=body_html,
        )
        if not result.success:
            result = await self.brevo.send(
                to_email=to_email, to_name=to_name,
                from_email=from_email, from_name=from_name,
                subject=subject, body_html=body_html,
                tag=tag,
            )
        if not result.success:
            result = await self.mailgun.send(
                to_email=to_email, to_name=to_name,
                from_email=from_email, from_name=from_name,
                subject=subject, body_html=body_html,
            )

        if result.success:
            self.csm.handle_send(lead_id, "email")

        return result

    def score_intent(self, contact: dict) -> int:
        """Simple intent score from enrichment signals (0–100).
        Full intent scoring (3rd-party signals) ships Sprint 4.
        """
        score = 0
        if contact.get("email_verified"):
            score += 20
        source = contact.get("enrichment_source", "")
        if source == "prospeo":
            score += 15
        elif source == "hunter":
            score += 10
        status = contact.get("global_status", "prospecting")
        if status == "engaged":
            score += 25
        elif status == "interested":
            score += 40
        elif status == "meeting_set":
            score += 60
        signals = contact.get("intent_signals") or []
        score += min(len(signals) * 5, 20)
        return min(score, 100)
