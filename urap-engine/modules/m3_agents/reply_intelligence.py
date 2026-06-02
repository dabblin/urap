"""Module III — Reply Intelligence Agent.

Parses incoming reply text, classifies sentiment via Claude Sonnet 4.6,
maps to a globalStatus update, fires Google Calendar on meeting_set,
and sends a Telegram alert on meeting_set or qualified.

Sentiment classes:
  meeting_request → globalStatus = meeting_set + Calendar + Telegram
  positive        → globalStatus = interested + Telegram (if qualified)
  neutral         → no change
  negative        → globalStatus = not_interested
  unsubscribe     → globalStatus = unsubscribe (all channels paused)
  out_of_office   → no change
"""
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from modules.m2_outreach.channel_state_machine import ChannelStateMachine
from tier3.telegram.client import notify_lead_qualified, notify_meeting_set
from tier3.gcalendar.client import create_discovery_call

CLAUDE_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL = "claude-sonnet-4-6"

VALID_SENTIMENTS = {"meeting_request", "positive", "neutral", "negative", "unsubscribe", "out_of_office"}


@dataclass
class ParseResult:
    lead_id: str
    channel: str
    sentiment: str
    confidence: float
    global_status_updated_to: str
    calendar_link: str
    telegram_sent: bool
    summary: str


class ReplyIntelligenceAgent:
    def __init__(self) -> None:
        self._csm = ChannelStateMachine()
        self._supabase = None

    def _db(self):
        if self._supabase is None:
            from supabase import create_client
            self._supabase = create_client(
                os.environ["SUPABASE_URL"],
                os.environ["SUPABASE_ANON_KEY"],
            )
        return self._supabase

    def _load_lead(self, lead_id: str) -> Optional[dict]:
        try:
            result = (
                self._db()
                .table("urap_contacts")
                .select("*")
                .eq("lead_id", lead_id)
                .limit(1)
                .execute()
            )
            rows = result.data or []
            return rows[0] if rows else None
        except Exception:
            return None

    # ── Sentiment classification ──────────────────────────────────────────────

    async def _classify_sentiment(self, reply_text: str) -> tuple[str, float, str]:
        """Classify reply sentiment. Falls back to keyword heuristics if no Claude key."""
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")

        if not api_key:
            return self._keyword_classify(reply_text)

        prompt = f"""Classify this B2B sales reply email as exactly one sentiment type.

Reply text:
\"\"\"
{reply_text[:1500]}
\"\"\"

Sentiment types:
- "meeting_request" — lead wants to schedule a call, meeting, or demo
- "positive" — interested, wants more info, open to conversation
- "neutral" — non-committal, unclear
- "negative" — not interested, bad timing, not relevant
- "unsubscribe" — explicitly wants to stop receiving emails
- "out_of_office" — automated away-message, no human decision

Return valid JSON only: {{"sentiment": "...", "confidence": 0.0, "summary": "one sentence"}}"""

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    CLAUDE_URL,
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": CLAUDE_MODEL,
                        "max_tokens": 256,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                    timeout=15,
                )
            if resp.status_code != 200:
                return self._keyword_classify(reply_text)
            data = resp.json()
            text = data["content"][0]["text"]
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                parsed = json.loads(match.group())
                sentiment = parsed.get("sentiment", "neutral")
                if sentiment not in VALID_SENTIMENTS:
                    sentiment = "neutral"
                return (
                    sentiment,
                    float(parsed.get("confidence", 0.7)),
                    parsed.get("summary", ""),
                )
        except Exception as e:
            print(f"[reply_intel] Claude error: {e}")

        return self._keyword_classify(reply_text)

    def _keyword_classify(self, reply_text: str) -> tuple[str, float, str]:
        """Heuristic fallback when Claude is not configured."""
        text = reply_text.lower()
        if any(w in text for w in ["unsubscribe", "remove me", "stop emailing", "opt out", "do not contact"]):
            return ("unsubscribe", 0.9, "Unsubscribe request detected via keyword match")
        if any(w in text for w in ["not interested", "no thanks", "not relevant", "not a fit", "pass on this"]):
            return ("negative", 0.8, "Negative response via keyword match")
        if any(w in text for w in ["schedule", "book a call", "calendar", "available", "let's chat", "set up a time"]):
            return ("meeting_request", 0.75, "Meeting request detected via keyword match")
        if any(w in text for w in ["out of office", "away", "on vacation", "will return", "auto-reply"]):
            return ("out_of_office", 0.9, "Out-of-office auto-reply detected")
        if any(w in text for w in ["interested", "tell me more", "sounds good", "curious", "learn more"]):
            return ("positive", 0.7, "Positive response via keyword match")
        return ("neutral", 0.4, "No strong signal — defaulting to neutral")

    # ── Main parse entry point ────────────────────────────────────────────────

    async def parse_reply(
        self,
        lead_id: str,
        channel: str,
        reply_text: str,
        tenant_id: str = "",
    ) -> ParseResult:
        """Parse a reply, update channel state, fire alerts. Main agent method."""
        sentiment, confidence, summary = await self._classify_sentiment(reply_text)

        # Map sentiment → CSM action → globalStatus
        csm_result: dict = {}
        if sentiment == "meeting_request":
            csm_result = self._csm.handle_meeting_set(lead_id)
            # Also mark the reply channel
            self._csm.handle_reply(lead_id, channel)
        elif sentiment in ("positive", "neutral", "out_of_office"):
            csm_result = self._csm.handle_reply(lead_id, channel)
        elif sentiment == "negative":
            # Direct DB update — CSM doesn't expose not_interested handler
            try:
                self._db().table("urap_contacts").update(
                    {"global_status": "not_interested"}
                ).eq("lead_id", lead_id).execute()
            except Exception:
                pass
            csm_result = {"global_status": "not_interested"}
        elif sentiment == "unsubscribe":
            csm_result = self._csm.handle_unsubscribe(lead_id)

        global_status = csm_result.get("global_status", "engaged")

        # Calendar: create discovery call when meeting is set
        calendar_link = ""
        if sentiment == "meeting_request" and global_status == "meeting_set":
            lead = self._load_lead(lead_id)
            if lead:
                # Default slot: next business day at 2pm ET
                tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
                slot_start = tomorrow.replace(hour=19, minute=0, second=0, microsecond=0).isoformat()
                calendar_link = create_discovery_call(
                    lead_name=lead.get("name", "Lead"),
                    lead_email=lead.get("email", ""),
                    company=lead.get("company", ""),
                    slot_start=slot_start,
                    context=reply_text[:300],
                )

        # Telegram alerts
        telegram_sent = False
        if global_status in ("meeting_set", "qualified"):
            lead = self._load_lead(lead_id)
            name = (lead or {}).get("name", lead_id)
            company = (lead or {}).get("company", "")
            title = (lead or {}).get("title", "")
            if global_status == "meeting_set":
                result = notify_meeting_set(lead_id, name, company, title, calendar_link)
            else:
                result = notify_lead_qualified(lead_id, name, company, title, 100)
            telegram_sent = result.get("status") == "sent"

        return ParseResult(
            lead_id=lead_id,
            channel=channel,
            sentiment=sentiment,
            confidence=confidence,
            global_status_updated_to=global_status,
            calendar_link=calendar_link,
            telegram_sent=telegram_sent,
            summary=summary,
        )
