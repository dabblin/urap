"""Module I — Reverse phone lookup.

Unlike the email enrichment waterfall, every layer here runs and its result is
merged with provenance. A phone number has several independent truths (who the
carrier says owns the line, who called us and said their name, what the public
web shows) and an operator needs to see them side by side to judge a caller.

Layers:
  1. offline    — libphonenumber: validity, region, timezone, national format. Free.
  2. internal   — our own Supabase records. First-party, highest trust.
  3. twilio     — Lookup v2: carrier, line type, CNAM subscriber name.
  4. numverify  — free-tier carrier/line type when Twilio is unconfigured.
  5. web        — Gemini grounded search over public listings. Opt-in (deep=True).

Compliance: this is caller-identification for inbound business contacts. Results
must not be used for credit, insurance, employment, or housing decisions — that
is an FCRA-regulated consumer report and none of these providers are a CRA.
"""
import os
import re
import sys
import asyncio
import logging
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from tier3.twilio import client as twilio_client
from tier3.numverify import client as numverify_client

logger = logging.getLogger(__name__)

# Tables that may hold a phone number, mapped to the columns worth returning.
# Verified against the live schema 2026-08-20 — urap_lead_distribution does not
# exist, and urap_contacts is not readable by the anon key currently in .env.
_INTERNAL_TABLES = (
    ("urap_contacts", "phone", ("lead_id", "name", "email", "company", "title", "phone")),
    ("urap_lead_list_items", "phone", ("company_name", "contact_name", "contact_title", "email", "phone", "website")),
    ("urap_campaign_list_contacts", "phone", ("lead_id", "name", "title", "company", "email", "phone")),
)

_NUMBER_TYPE_LABELS = {
    0: "fixed_line",
    1: "mobile",
    2: "fixed_line_or_mobile",
    3: "toll_free",
    4: "premium_rate",
    5: "shared_cost",
    6: "voip",
    7: "personal_number",
    8: "pager",
    9: "uan",
    10: "voicemail",
    -1: "unknown",
}


_INTERNAL_PHONE_COL = "phone"


def _digits(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def _supabase_reason(exc: Exception) -> str:
    """Condense a postgrest APIError to something an operator can act on."""
    code = getattr(exc, "code", "") or ""
    message = getattr(exc, "message", "") or ""
    hint = getattr(exc, "hint", "") or ""
    if message:
        return f"[{code}] {message}{f' — {hint}' if hint else ''}"[:300]
    return str(exc)[:300]


class ReversePhoneService:
    def __init__(self) -> None:
        self._supabase = None

    def _db(self):
        if self._supabase is None:
            from supabase import create_client
            url = os.environ["SUPABASE_URL"]
            key = os.environ["SUPABASE_ANON_KEY"]
            self._supabase = create_client(url, key)
        return self._supabase

    # ── Layer 1: offline parse ────────────────────────────────────────────────

    def _parse(self, raw: str, country: str) -> dict:
        import phonenumbers
        from phonenumbers import geocoder, carrier, timezone

        try:
            parsed = phonenumbers.parse(raw, country)
        except Exception as exc:
            return {"ok": False, "error": f"unparseable: {exc}"}

        valid = phonenumbers.is_valid_number(parsed)
        return {
            "ok": True,
            "valid": valid,
            "e164": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164),
            "national": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL),
            "country_code": parsed.country_code,
            "region": geocoder.description_for_number(parsed, "en") or "",
            "carrier_hint": carrier.name_for_number(parsed, "en") or "",
            "line_type_hint": _NUMBER_TYPE_LABELS.get(phonenumbers.number_type(parsed), "unknown"),
            "timezones": list(timezone.time_zones_for_number(parsed)),
        }

    # ── Layer 2: internal first-party records ─────────────────────────────────

    def _internal(self, e164: str) -> dict:
        """Search our own tables for the number.

        Phone formatting is inconsistent across ingestion sources and PostgREST
        cannot strip non-digits inside a filter, so we query the common written
        forms and then confirm each hit by comparing normalized digits.
        """
        target = _digits(e164)[-10:]
        if len(target) != 10:
            return {"status": "skipped", "reason": "not a 10-digit NANP number", "matches": []}

        try:
            db = self._db()
        except Exception as exc:
            return {"status": "error", "reason": str(exc), "matches": []}

        a, b, c = target[:3], target[3:6], target[6:]
        variants = (
            e164, f"1{target}", target,
            f"{a}-{b}-{c}", f"({a}) {b}-{c}", f"({a}){b}-{c}",
            f"{a}.{b}.{c}", f"{a} {b} {c}",
        )
        # Values are double-quoted so parentheses and dots are not parsed as
        # PostgREST operator syntax.
        or_filter = ",".join(f'{_INTERNAL_PHONE_COL}.ilike."%{v}%"' for v in variants)

        matches: list[dict] = []
        errors: list[dict] = []
        searched = 0
        for table, column, columns in _INTERNAL_TABLES:
            try:
                rows = (
                    db.table(table)
                    .select(",".join(columns))
                    .or_(or_filter)
                    .limit(25)
                    .execute()
                ).data or []
                searched += 1
            except Exception as exc:
                reason = _supabase_reason(exc)
                logger.warning("[reverse_phone] internal search failed on %s: %s", table, reason)
                errors.append({"table": table, "reason": reason})
                continue

            for row in rows:
                if _digits(str(row.get(column) or ""))[-10:] != target:
                    continue
                matches.append({"table": table, **{k: row.get(k) for k in columns}})

        if searched == 0:
            return {
                "status": "error",
                "reason": "no internal table could be searched",
                "errors": errors,
                "matches": [],
            }

        return {
            "status": "ok" if not errors else "partial",
            "searched_tables": searched,
            "errors": errors,
            "matches": matches,
        }

    # ── Layer 2b: inbound voice call log ──────────────────────────────────────

    def _voice_log(self, e164: str) -> dict:
        """Search the AI receptionist's call log — the record of who actually
        called us and what they said they wanted. Optional: set
        VOICE_CALL_LOG_SHEET_ID to enable."""
        sheet_id = os.getenv("VOICE_CALL_LOG_SHEET_ID", "")
        if not sheet_id:
            return {"status": "not_configured", "reason": "VOICE_CALL_LOG_SHEET_ID not set", "matches": []}

        target = _digits(e164)[-10:]
        try:
            import google.auth
            from googleapiclient.discovery import build

            creds, _ = google.auth.default(
                scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
            )
            service = build("sheets", "v4", credentials=creds)
            result = (
                service.spreadsheets()
                .values()
                .get(spreadsheetId=sheet_id, range=os.getenv("VOICE_CALL_LOG_RANGE", "A:G"))
                .execute()
            )
        except Exception as exc:
            return {"status": "error", "reason": str(exc)[:200], "matches": []}

        rows = result.get("values") or []
        if not rows:
            return {"status": "ok", "matches": []}

        header = [h.strip().lower() for h in rows[0]]
        matches = []
        for row in rows[1:]:
            record = dict(zip(header, row))
            phone = record.get("caller phone") or record.get("phone") or ""
            if _digits(phone)[-10:] != target:
                continue
            matches.append(record)

        return {"status": "ok", "matches": matches}

    # ── Layer 3/4: carrier + subscriber name ──────────────────────────────────

    async def _twilio(self, e164: str) -> dict:
        result = await twilio_client.lookup_number(e164)
        if not result["ok"]:
            status = "not_configured" if not twilio_client.lookup_is_configured() else "error"
            return {"status": status, "reason": result["error"], "data": {}}

        data = result["data"] or {}
        lti = data.get("line_type_intelligence") or {}
        cnam = data.get("caller_name") or {}
        return {
            "status": "ok",
            "data": {
                "carrier": lti.get("carrier_name") or "",
                "line_type": lti.get("type") or "",
                "caller_name": cnam.get("caller_name") or "",
                "caller_type": cnam.get("caller_type") or "",
                "valid": data.get("valid"),
            },
        }

    async def _numverify(self, e164: str, country: str) -> dict:
        result = await numverify_client.validate_number(e164, country)
        if not result["ok"]:
            status = "not_configured" if not numverify_client.is_configured() else "error"
            return {"status": status, "reason": result["error"], "data": {}}

        data = result["data"] or {}
        return {
            "status": "ok",
            "data": {
                "carrier": data.get("carrier") or "",
                "line_type": data.get("line_type") or "",
                "location": data.get("location") or "",
                "valid": data.get("valid"),
            },
        }

    # ── Layer 5: public web (opt-in) ──────────────────────────────────────────

    async def _web(self, e164: str, national: str) -> dict:
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            return {"status": "not_configured", "reason": "GEMINI_API_KEY not set", "data": {}}

        prompt = (
            f"Search the public web for the US phone number {national} (also written {e164}). "
            "Report only what is actually published on public pages: any business name, "
            "person's name, website, or address associated with it, and whether it is "
            "reported as spam or a robocall. Cite the page for each claim. "
            "If nothing credible is published, say exactly: NO PUBLIC RECORD FOUND. "
            "Never guess or infer an identity."
        )

        import httpx
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                resp = await client.post(
                    "https://generativelanguage.googleapis.com/v1beta/models/"
                    "gemini-flash-latest:generateContent",
                    headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "tools": [{"google_search": {}}],
                    },
                )
        except Exception as exc:
            return {"status": "error", "reason": str(exc), "data": {}}

        if resp.status_code != 200:
            return {"status": "error", "reason": f"HTTP {resp.status_code}: {resp.text[:200]}", "data": {}}

        payload = resp.json()
        try:
            candidate = payload["candidates"][0]
            text = "".join(
                part.get("text", "") for part in candidate["content"]["parts"]
            ).strip()
        except (KeyError, IndexError):
            return {"status": "error", "reason": "unexpected Gemini response shape", "data": {}}

        sources: list[str] = []
        grounding = (payload["candidates"][0] or {}).get("groundingMetadata") or {}
        for chunk in grounding.get("groundingChunks") or []:
            uri = (chunk.get("web") or {}).get("uri")
            if uri:
                sources.append(uri)

        return {
            "status": "ok",
            "data": {
                "summary": text,
                "found": "NO PUBLIC RECORD FOUND" not in text.upper(),
                "sources": sources[:10],
            },
        }

    # ── Orchestration ─────────────────────────────────────────────────────────

    def _resolve_identity(self, internal: dict, voice: dict, twilio: dict, web: dict) -> dict:
        """Pick the best available name, most-trusted source first."""
        # A person's name is a better answer than the business they work at,
        # so exhaust contact names across every match before falling back.
        for field in ("name", "contact_name", "company_name", "company"):
            for match in internal.get("matches") or []:
                name = (match.get(field) or "").strip()
                if name:
                    return {
                        "name": name,
                        "source": f"internal:{match['table']}",
                        "confidence": "high",
                    }

        for call in voice.get("matches") or []:
            name = call.get("caller name") or call.get("name")
            if name:
                return {
                    "name": name,
                    "source": "voice_call_log",
                    # Self-reported to the receptionist — never carrier-verified.
                    "confidence": "medium",
                    "note": "caller stated this name on a call; not independently verified",
                }

        cnam = (twilio.get("data") or {}).get("caller_name")
        if cnam:
            return {
                "name": cnam,
                "source": "twilio:cnam",
                "confidence": "high",
            }

        if (web.get("data") or {}).get("found"):
            return {
                "name": "",
                "source": "web",
                "confidence": "low",
                "note": "see web.summary — unstructured, verify before acting",
            }

        return {"name": "", "source": "", "confidence": "none"}

    async def lookup(
        self,
        number: str,
        country: str = "US",
        deep: bool = False,
    ) -> dict:
        parsed = self._parse(number, country)
        if not parsed["ok"]:
            return {"input": number, "valid": False, "error": parsed["error"]}

        e164 = parsed["e164"]
        national = parsed["national"]

        # Providers bill per lookup — never spend a call on a number the
        # offline parser already knows is not dialable.
        if not parsed["valid"]:
            return {
                "input": number,
                "e164": e164,
                "national": national,
                "valid": False,
                "identity": {"name": "", "source": "", "confidence": "none"},
                "line": {"carrier": "", "type": parsed["line_type_hint"], "caller_type": ""},
                "location": {
                    "region": parsed["region"],
                    "country_code": parsed["country_code"],
                    "timezones": parsed["timezones"],
                },
                "internal_matches": [],
                "voice_calls": [],
                "sources": {"offline": {"status": "ok", "reason": "number is not valid — no provider was queried"}},
                "web": {},
            }

        internal, voice, twilio, numverify, web = await asyncio.gather(
            asyncio.to_thread(self._internal, e164),
            asyncio.to_thread(self._voice_log, e164),
            self._twilio(e164),
            self._numverify(e164, country),
            self._web(e164, national) if deep else _skipped("deep=false"),
        )

        tw = twilio.get("data") or {}
        nv = numverify.get("data") or {}

        return {
            "input": number,
            "e164": e164,
            "national": national,
            "valid": parsed["valid"],
            "identity": self._resolve_identity(internal, voice, twilio, web),
            "line": {
                # Live carrier data wins over the offline hint, which cannot
                # distinguish mobile from landline anywhere in the NANP.
                "carrier": tw.get("carrier") or nv.get("carrier") or parsed["carrier_hint"] or "",
                "type": tw.get("line_type") or nv.get("line_type") or parsed["line_type_hint"],
                "caller_type": tw.get("caller_type") or "",
            },
            "location": {
                "region": parsed["region"] or nv.get("location") or "",
                "country_code": parsed["country_code"],
                "timezones": parsed["timezones"],
            },
            "internal_matches": internal.get("matches") or [],
            "voice_calls": voice.get("matches") or [],
            "sources": {
                "offline": {"status": "ok"},
                "internal": {
                    "status": internal.get("status"),
                    "reason": internal.get("reason", ""),
                    "errors": internal.get("errors") or [],
                },
                "voice_call_log": {"status": voice.get("status"), "reason": voice.get("reason", "")},
                "twilio": {"status": twilio.get("status"), "reason": twilio.get("reason", "")},
                "numverify": {"status": numverify.get("status"), "reason": numverify.get("reason", "")},
                "web": {"status": web.get("status"), "reason": web.get("reason", "")},
            },
            "web": web.get("data") or {},
        }


async def _skipped(reason: str) -> dict:
    return {"status": "skipped", "reason": reason, "data": {}}
