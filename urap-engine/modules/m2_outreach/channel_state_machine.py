"""Module II — Omni-Channel Outreach: channel state machine.

Core rule: a reply on ANY channel immediately pauses all other channel tasks
and upgrades globalStatus. This prevents double-touch after a lead responds.

Channel states
  email:    idle | sent | opened | replied | bounced | paused
  sms:      idle | sent | replied | opted_out | paused
  linkedin: idle | connected | messaged | replied | paused
  voice:    idle | dialed | answered | voicemail | paused

Global status progression
  prospecting → engaged → interested → meeting_set → qualified
  Any state   → not_interested | unsubscribe
"""
import os
import sys
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

CHANNELS = ("email", "sms", "linkedin", "voice")

GLOBAL_STATUS_RANK = {
    "prospecting": 0,
    "engaged": 1,
    "interested": 2,
    "meeting_set": 3,
    "qualified": 4,
    "not_interested": -1,
    "unsubscribe": -2,
}


def _default_channel_state() -> dict:
    return {ch: "idle" for ch in CHANNELS}


class ChannelStateMachine:
    def __init__(self) -> None:
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
                .select("lead_id,global_status,channel_state")
                .eq("lead_id", lead_id)
                .limit(1)
                .execute()
            )
            rows = result.data or []
            return rows[0] if rows else None
        except Exception:
            return None

    def _save_lead(self, lead_id: str, global_status: str, channel_state: dict) -> None:
        try:
            self._db().table("urap_contacts").update(
                {"global_status": global_status, "channel_state": channel_state}
            ).eq("lead_id", lead_id).execute()
        except Exception:
            pass

    def _upgrade_status(self, current: str, candidate: str) -> str:
        """Advance to candidate only if it outranks current. Never downgrade."""
        if GLOBAL_STATUS_RANK.get(candidate, -99) > GLOBAL_STATUS_RANK.get(current, -99):
            return candidate
        return current

    def handle_reply(self, lead_id: str, channel: str) -> dict:
        """Call when a reply arrives on any channel.
        Pauses all other channels, upgrades globalStatus to 'interested'.
        Returns updated state dict.
        """
        lead = self._load_lead(lead_id) or {}
        ch_state = lead.get("channel_state") or _default_channel_state()
        global_status = lead.get("global_status", "prospecting")

        ch_state[channel] = "replied"
        for other in CHANNELS:
            if other != channel and ch_state.get(other) not in ("idle", "replied", "bounced", "opted_out"):
                ch_state[other] = "paused"

        global_status = self._upgrade_status(global_status, "interested")
        self._save_lead(lead_id, global_status, ch_state)
        return {"lead_id": lead_id, "global_status": global_status, "channel_state": ch_state}

    def handle_send(self, lead_id: str, channel: str) -> dict:
        lead = self._load_lead(lead_id) or {}
        ch_state = lead.get("channel_state") or _default_channel_state()
        global_status = self._upgrade_status(lead.get("global_status", "prospecting"), "engaged")
        ch_state[channel] = "sent"
        self._save_lead(lead_id, global_status, ch_state)
        return {"lead_id": lead_id, "global_status": global_status, "channel_state": ch_state}

    def handle_open(self, lead_id: str) -> dict:
        lead = self._load_lead(lead_id) or {}
        ch_state = lead.get("channel_state") or _default_channel_state()
        if ch_state.get("email") == "sent":
            ch_state["email"] = "opened"
        global_status = self._upgrade_status(lead.get("global_status", "prospecting"), "interested")
        self._save_lead(lead_id, global_status, ch_state)
        return {"lead_id": lead_id, "global_status": global_status, "channel_state": ch_state}

    def handle_bounce(self, lead_id: str) -> dict:
        lead = self._load_lead(lead_id) or {}
        ch_state = lead.get("channel_state") or _default_channel_state()
        ch_state["email"] = "bounced"
        global_status = lead.get("global_status", "prospecting")
        self._save_lead(lead_id, global_status, ch_state)
        return {"lead_id": lead_id, "global_status": global_status, "channel_state": ch_state}

    def handle_unsubscribe(self, lead_id: str) -> dict:
        lead = self._load_lead(lead_id) or {}
        ch_state = {ch: "paused" for ch in CHANNELS}
        self._save_lead(lead_id, "unsubscribe", ch_state)
        return {"lead_id": lead_id, "global_status": "unsubscribe", "channel_state": ch_state}

    def handle_meeting_set(self, lead_id: str) -> dict:
        lead = self._load_lead(lead_id) or {}
        ch_state = lead.get("channel_state") or _default_channel_state()
        global_status = self._upgrade_status(lead.get("global_status", "prospecting"), "meeting_set")
        self._save_lead(lead_id, global_status, ch_state)
        return {"lead_id": lead_id, "global_status": global_status, "channel_state": ch_state}

    def can_send(self, lead_id: str, channel: str) -> bool:
        """Check if a channel is in a sendable state before queuing outreach."""
        lead = self._load_lead(lead_id)
        if not lead:
            return True  # new lead — allow
        ch_state = lead.get("channel_state") or _default_channel_state()
        blocked = {"replied", "paused", "opted_out", "bounced", "unsubscribe"}
        return ch_state.get(channel, "idle") not in blocked
