"""Numverify phone validation client — free-tier carrier/line-type fallback.

Used when Twilio Lookup is unconfigured or returns no carrier data.
Free tier: 100 lookups/month, no CC. Returns carrier + line type + location,
but no subscriber name — Twilio CNAM remains the only name source.

API docs: https://numverify.com/documentation
"""
import os
import logging

logger = logging.getLogger(__name__)

NUMVERIFY_BASE = "https://apilayer.net/api/validate"


def is_configured() -> bool:
    return bool(os.getenv("NUMVERIFY_API_KEY", ""))


async def validate_number(e164: str, country_code: str = "US") -> dict:
    """Return {ok, data, error}. Never raises — this is one waterfall layer."""
    api_key = os.getenv("NUMVERIFY_API_KEY", "")
    if not api_key:
        return {"ok": False, "data": {}, "error": "NUMVERIFY_API_KEY not set"}

    import httpx
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                NUMVERIFY_BASE,
                params={
                    "access_key": api_key,
                    "number": e164.lstrip("+"),
                    "country_code": country_code,
                    "format": 1,
                },
            )
    except Exception as exc:
        logger.error("[numverify] transport error: %s", exc)
        return {"ok": False, "data": {}, "error": str(exc)}

    if resp.status_code != 200:
        return {"ok": False, "data": {}, "error": f"HTTP {resp.status_code}"}

    data = resp.json()
    # Numverify signals auth/quota failures in the body with HTTP 200.
    if isinstance(data, dict) and data.get("success") is False:
        info = (data.get("error") or {}).get("info", "unknown numverify error")
        return {"ok": False, "data": {}, "error": info}

    return {"ok": True, "data": data, "error": ""}
