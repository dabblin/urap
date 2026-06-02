"""Tier 3 — Google Calendar: create discovery call events on meeting_set triggers.

Setup: attach a Google service account with Calendar write access or use ADC.
On Cloud Run, ADC uses the attached service account automatically.
Locally: set GOOGLE_APPLICATION_CREDENTIALS to a service account JSON key.

Required env vars (optional — falls back to ADC):
  GOOGLE_APPLICATION_CREDENTIALS — path to service account JSON (local dev only)
  GOOGLE_CALENDAR_ID             — calendar to write events to (default: djdabblin@gmail.com)
"""
import os
from datetime import datetime, timedelta

CALENDAR_ID = os.environ.get("GOOGLE_CALENDAR_ID", "djdabblin@gmail.com")
SCOPES = ["https://www.googleapis.com/auth/calendar"]
SLOT_MINUTES = 30


def _get_service():
    import google.auth
    from googleapiclient.discovery import build
    creds, _ = google.auth.default(scopes=SCOPES)
    return build("calendar", "v3", credentials=creds)


def create_discovery_call(
    lead_name: str,
    lead_email: str,
    company: str,
    slot_start: str,
    context: str = "",
) -> str:
    """Create a 30-min discovery call event. Returns HTML link or '' on failure.

    slot_start: ISO 8601 datetime string (e.g. "2026-06-01T14:00:00-05:00")
    """
    try:
        service = _get_service()
        start = datetime.fromisoformat(slot_start)
        end = start + timedelta(minutes=SLOT_MINUTES)
        event = {
            "summary": f"Discovery Call: {lead_name} @ {company}",
            "description": f"Lead email: {lead_email}\nContext: {context}",
            "start": {"dateTime": start.isoformat(), "timeZone": "America/New_York"},
            "end": {"dateTime": end.isoformat(), "timeZone": "America/New_York"},
            "attendees": [{"email": lead_email}] if lead_email else [],
            "reminders": {
                "useDefault": False,
                "overrides": [{"method": "popup", "minutes": 15}],
            },
        }
        result = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        return result.get("htmlLink", "")
    except Exception as e:
        print(f"[gcalendar] ERROR: {e}")
        return ""
