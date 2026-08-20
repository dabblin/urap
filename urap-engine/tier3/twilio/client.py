"""Twilio client — URAP Sprint 5 Power Dialer + SMS + geo-routing."""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

ACCOUNT_SID   = os.getenv("TWILIO_ACCOUNT_SID", "")
AUTH_TOKEN    = os.getenv("TWILIO_AUTH_TOKEN", "")
FROM_NUMBER   = os.getenv("TWILIO_PHONE_NUMBER", "")

# Regional number overrides keyed by ISO country code.
# Populated via TWILIO_REGIONAL_NUMBERS env var: "US:+12125550100,CA:+14165550100"
def _load_regional_numbers() -> dict[str, str]:
    raw = os.getenv("TWILIO_REGIONAL_NUMBERS", "")
    mapping: dict[str, str] = {}
    for pair in raw.split(","):
        parts = pair.strip().split(":")
        if len(parts) == 2:
            mapping[parts[0].upper()] = parts[1]
    return mapping

REGIONAL_NUMBERS: dict[str, str] = _load_regional_numbers()


def _get_client():
    if not ACCOUNT_SID or not AUTH_TOKEN:
        return None
    try:
        from twilio.rest import Client
        return Client(ACCOUNT_SID, AUTH_TOKEN)
    except ImportError:
        logger.warning("[twilio] twilio package not installed")
        return None


# ── Geo-routing ───────────────────────────────────────────────────────────────

def resolve_from_number(country_code: str = "US") -> str:
    """Return the best outbound number for the given ISO country code."""
    return REGIONAL_NUMBERS.get(country_code.upper(), FROM_NUMBER)


def geolocate_country(ip_address: str) -> str:
    """
    Light-weight geo lookup using ipapi.co (free, no key required, 1k req/day).
    Falls back to 'US' on any error.
    """
    if not ip_address or ip_address in ("127.0.0.1", "::1"):
        return "US"
    try:
        import httpx
        resp = httpx.get(f"https://ipapi.co/{ip_address}/country/", timeout=3)
        if resp.status_code == 200 and len(resp.text.strip()) == 2:
            return resp.text.strip().upper()
    except Exception:
        pass
    return "US"


# ── Voice / Power Dialer ──────────────────────────────────────────────────────

def dial_lead(
    to_number: str,
    lead_id: str,
    agent_number: str = "",
    country_code: str = "US",
    status_callback_url: str = "",
) -> dict:
    """
    Initiate an outbound call from the URAP power dialer.
    Connects the SDR (agent_number or FROM_NUMBER) to the lead.

    Returns: {success, call_sid, status, error}
    """
    client = _get_client()
    if not client:
        return {"success": False, "call_sid": "", "status": "not_configured",
                "error": "TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN not set"}

    from_num = agent_number or resolve_from_number(country_code)
    if not from_num:
        return {"success": False, "call_sid": "", "status": "error",
                "error": "No Twilio phone number configured"}

    try:
        params: dict = {
            "to": to_number,
            "from_": from_num,
            "twiml": f'<Response><Say>Connecting call for lead {lead_id}.</Say></Response>',
        }
        if status_callback_url:
            params["status_callback"] = status_callback_url
            params["status_callback_method"] = "POST"

        call = client.calls.create(**params)
        return {"success": True, "call_sid": call.sid, "status": call.status, "error": ""}
    except Exception as exc:
        logger.error("[twilio] dial_lead error: %s", exc)
        return {"success": False, "call_sid": "", "status": "error", "error": str(exc)}


def get_call_status(call_sid: str) -> dict:
    """Return current status of a call by SID."""
    client = _get_client()
    if not client:
        return {"call_sid": call_sid, "status": "not_configured"}
    try:
        call = client.calls(call_sid).fetch()
        return {
            "call_sid": call_sid,
            "status": call.status,
            "duration": call.duration,
            "direction": call.direction,
        }
    except Exception as exc:
        return {"call_sid": call_sid, "status": "error", "error": str(exc)}


def end_call(call_sid: str) -> dict:
    """Hang up an active call."""
    client = _get_client()
    if not client:
        return {"success": False, "error": "not_configured"}
    try:
        from twilio.rest import Client as _C  # noqa — already imported above
        client.calls(call_sid).update(status="completed")
        return {"success": True, "call_sid": call_sid}
    except Exception as exc:
        return {"success": False, "call_sid": call_sid, "error": str(exc)}


# ── SMS ───────────────────────────────────────────────────────────────────────

def send_sms(
    to_number: str,
    body: str,
    lead_id: str = "",
    country_code: str = "US",
) -> dict:
    """
    Send an outbound SMS.  Requires TCPA consent — caller must verify before use.

    Returns: {success, message_sid, status, error}
    """
    client = _get_client()
    if not client:
        return {"success": False, "message_sid": "", "status": "not_configured",
                "error": "TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN not set"}

    from_num = resolve_from_number(country_code)
    if not from_num:
        return {"success": False, "message_sid": "", "status": "error",
                "error": "No Twilio phone number configured"}

    try:
        msg = client.messages.create(to=to_number, from_=from_num, body=body)
        return {"success": True, "message_sid": msg.sid, "status": msg.status, "error": ""}
    except Exception as exc:
        logger.error("[twilio] send_sms error lead=%s: %s", lead_id, exc)
        return {"success": False, "message_sid": "", "status": "error", "error": str(exc)}


# ── Convenience helpers ───────────────────────────────────────────────────────

def is_configured() -> bool:
    return bool(ACCOUNT_SID and AUTH_TOKEN and FROM_NUMBER)


# ── Lookup v2 — reverse phone intelligence ────────────────────────────────────

LOOKUP_BASE = "https://lookups.twilio.com/v2/PhoneNumbers"

# Packages billed per lookup. caller_name is US-only (CNAM).
LOOKUP_FIELDS = ("line_type_intelligence", "caller_name")


def lookup_is_configured() -> bool:
    """Lookup only needs the credential pair — no outbound number required."""
    return bool(ACCOUNT_SID and AUTH_TOKEN)


async def lookup_number(e164: str, fields: tuple[str, ...] = LOOKUP_FIELDS) -> dict:
    """Twilio Lookup v2 — carrier, line type, and CNAM caller name.

    Returns {ok, data, error}. Never raises: the caller treats this as one
    layer of a waterfall and must survive an unconfigured or failing provider.
    """
    if not lookup_is_configured():
        return {"ok": False, "data": {}, "error": "TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN not set"}

    import httpx
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{LOOKUP_BASE}/{e164}",
                params={"Fields": ",".join(fields)},
                auth=(ACCOUNT_SID, AUTH_TOKEN),
            )
    except Exception as exc:
        logger.error("[twilio] lookup_number transport error: %s", exc)
        return {"ok": False, "data": {}, "error": str(exc)}

    if resp.status_code != 200:
        return {"ok": False, "data": {}, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}

    return {"ok": True, "data": resp.json(), "error": ""}
