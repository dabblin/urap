"""Tier 3 — Telegram alerts for URAP revenue events.

Required env vars:
  TELEGRAM_BOT_TOKEN   — Gravity-Claw bot token (from BotFather)
  TELEGRAM_DCT_CHAT_ID — CEO's personal Telegram user ID (integer)
"""
import os
from datetime import datetime, timezone

import httpx

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_DCT_CHAT_ID = os.environ.get("TELEGRAM_DCT_CHAT_ID", "")


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def send_telegram(message: str) -> dict:
    """POST a message to the DCT alert chat. Silent-fails — never raises."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_DCT_CHAT_ID:
        return {"status": "not_configured"}
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        resp = httpx.post(
            url,
            json={"chat_id": TELEGRAM_DCT_CHAT_ID, "text": message, "parse_mode": "HTML"},
            timeout=5,
        )
        if resp.status_code == 200:
            return {"status": "sent"}
        return {"status": "api_error", "code": resp.status_code}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def notify_lead_qualified(lead_id: str, name: str, company: str, title: str, score: int) -> dict:
    msg = (
        "🏆 <b>QUALIFIED LEAD — URAP</b>\n"
        f"👤 {name} — {title} @ {company}\n"
        f"📊 Intent Score: <b>{score}/100</b>\n"
        f"🆔 Lead: <code>{lead_id}</code>\n"
        f"🕐 {_now_utc()}"
    )
    return send_telegram(msg)


def notify_meeting_set(lead_id: str, name: str, company: str, title: str, calendar_link: str = "") -> dict:
    cal_line = f'\n🔗 <a href="{calendar_link}">Calendar Event</a>' if calendar_link else ""
    msg = (
        "📅 <b>MEETING SET — URAP</b>\n"
        f"👤 {name} — {title} @ {company}\n"
        f"🆔 Lead: <code>{lead_id}</code>{cal_line}\n"
        f"🕐 {_now_utc()}"
    )
    return send_telegram(msg)


def notify_warp_job_done(icp_label: str, leads_found: int, sequences_queued: int) -> dict:
    msg = (
        "⚡ <b>WARP MODE COMPLETE — URAP</b>\n"
        f"🎯 ICP: {icp_label}\n"
        f"👥 Leads found: <b>{leads_found}</b>\n"
        f"📬 Sequences queued: <b>{sequences_queued}</b>\n"
        f"🕐 {_now_utc()}"
    )
    return send_telegram(msg)
