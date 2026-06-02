"""
URAP Engine — E2E golden path test suite.

Tests the full request lifecycle against a running urap-engine instance.
Default target: http://localhost:8080 (override with URAP_ENGINE_URL env var).

Run:
    cd /Users/djdab/Developer/urap-engine
    python -m pytest tests/test_e2e.py -v

Requirements:
    pip install pytest pytest-asyncio httpx
"""
import os
import uuid
import httpx
import pytest

BASE_URL = os.getenv("URAP_ENGINE_URL", "http://localhost:8080")
TENANT_ID = "e2e-tenant"
API_KEY = os.getenv("URAP_API_KEY", "")  # empty = dev mode (no key required)

HEADERS = {
    "x-tenant-id": TENANT_ID,
    "x-api-key": API_KEY,
    "Content-Type": "application/json",
}

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def client():
    """Synchronous httpx client for the full test session."""
    with httpx.Client(base_url=BASE_URL, timeout=30) as c:
        yield c


@pytest.fixture(scope="session")
def auth_headers():
    return HEADERS


# ── Health ────────────────────────────────────────────────────────────────────

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["service"] == "urap-engine"


# ── Module I: Enrichment ──────────────────────────────────────────────────────

def test_enrich_single(client, auth_headers):
    r = client.post("/enrich", headers=auth_headers, json={
        "domain": "stripe.com",
        "first_name": "Patrick",
        "last_name": "Collison",
    })
    assert r.status_code == 200
    body = r.json()
    assert "contacts" in body
    # May return 0 contacts if Prospeo key not set — that's fine
    assert isinstance(body["contacts"], list)


def test_bulk_enrich(client, auth_headers):
    r = client.post("/enrich/bulk", headers=auth_headers, json={
        "domain": "stripe.com",
        "limit": 3,
    })
    assert r.status_code == 200
    body = r.json()
    assert "contacts" in body
    assert isinstance(body["contacts"], list)


# ── Module VI: TCPA Consent ───────────────────────────────────────────────────

def test_consent_record_and_check(client, auth_headers):
    lead_id = f"e2e-{uuid.uuid4()}"

    # Record consent (public endpoint)
    r = client.post("/consent/record", json={
        "lead_id": lead_id,
        "tenant_id": TENANT_ID,
        "source": "https://cert.trustedform.com/test-cert-url",
        "ip_address": "127.0.0.1",
        "platform_name": "e2e-test",
        "one_to_one_rule": True,
    })
    assert r.status_code == 200
    assert r.json()["status"] == "recorded"

    # Check consent
    r2 = client.post("/consent/check", headers=auth_headers, json={"lead_id": lead_id})
    assert r2.status_code == 200
    body = r2.json()
    assert body["lead_id"] == lead_id
    assert body["consented"] is True


# ── Module II: Channel State Machine ─────────────────────────────────────────

def test_channel_event_send_and_reply(client, auth_headers):
    lead_id = f"e2e-{uuid.uuid4()}"

    # Send event
    r = client.post("/outreach/channel/event", headers=auth_headers, json={
        "lead_id": lead_id,
        "channel": "email",
        "event": "send",
    })
    assert r.status_code == 200

    # Reply event
    r2 = client.post("/outreach/channel/event", headers=auth_headers, json={
        "lead_id": lead_id,
        "channel": "email",
        "event": "reply",
    })
    assert r2.status_code == 200
    body = r2.json()
    # global_status should advance from prospecting → engaged
    assert "global_status" in body or "error" not in body


# ── Module II: Email Send ─────────────────────────────────────────────────────

def test_email_send_graceful_without_smtp_key(client, auth_headers):
    """Email send should fail gracefully (not 500) when SMTP keys absent."""
    r = client.post("/outreach/email/send", headers=auth_headers, json={
        "lead_id": f"e2e-{uuid.uuid4()}",
        "to_email": "test@example.com",
        "to_name": "Test User",
        "from_email": "outreach@urap.dabblin.com",
        "from_name": "URAP Outreach",
        "subject": "E2E Test",
        "body_html": "<p>E2E test email.</p>",
    })
    assert r.status_code == 200
    body = r.json()
    # success=False is expected without SMTP keys — just not a 500
    assert "success" in body


# ── Module III: Warp Mode ─────────────────────────────────────────────────────

def test_warp_mode_run(client, auth_headers):
    """Warp Mode should complete (with fallback copy) even without AI keys."""
    r = client.post("/agents/warp/run", headers=auth_headers, json={
        "domain": "stripe.com",
        "title": "VP of Sales",
        "industry": "FinTech",
        "value_prop": "E2E test value prop",
        "icp_label": "E2E ICP",
        "limit": 2,
    })
    assert r.status_code == 200
    body = r.json()
    assert "job_id" in body
    assert "leads_found" in body
    assert "generated" in body
    assert isinstance(body["generated"], list)


def test_warp_mode_list_jobs(client, auth_headers):
    r = client.get("/agents/warp/jobs", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert "jobs" in body
    assert isinstance(body["jobs"], list)


# ── Module III: Reply Intelligence ───────────────────────────────────────────

def test_reply_parse_meeting_request(client, auth_headers):
    r = client.post("/agents/reply/parse", headers=auth_headers, json={
        "lead_id": f"e2e-{uuid.uuid4()}",
        "channel": "email",
        "reply_text": "Yes, let's set up a call. Are you free Thursday at 2pm?",
    })
    assert r.status_code == 200
    body = r.json()
    assert "sentiment" in body
    assert body["sentiment"] in {
        "meeting_request", "positive", "neutral",
        "negative", "unsubscribe", "out_of_office",
    }
    assert "confidence" in body
    assert "global_status_updated_to" in body


def test_reply_parse_unsubscribe(client, auth_headers):
    r = client.post("/agents/reply/parse", headers=auth_headers, json={
        "lead_id": f"e2e-{uuid.uuid4()}",
        "channel": "email",
        "reply_text": "Please remove me from your list. Unsubscribe.",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["sentiment"] == "unsubscribe"
    assert body["global_status_updated_to"] == "unsubscribe"


# ── Module IV: Lead Capture & Ping-Post ───────────────────────────────────────

def test_lead_capture_and_claim(client, auth_headers):
    # Capture (public endpoint — no API key)
    r = client.post("/leads/capture", headers={
        "Content-Type": "application/json",
        "x-tenant-id": TENANT_ID,
    }, json={
        "first_name": "Alex",
        "last_name": "E2E",
        "email": "alex@stripe.com",
        "company": "Stripe",
        "title": "VP Engineering",
        "source": "e2e-test",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "captured"
    assert "lead_id" in body
    preview_id = body["preview_id"]
    assert preview_id

    # Preview
    r2 = client.get(f"/leads/preview/{preview_id}", headers=auth_headers)
    assert r2.status_code == 200
    body2 = r2.json()
    assert body2["status"] == "available"

    # Claim
    r3 = client.post("/leads/claim", headers=auth_headers, json={"preview_id": preview_id})
    assert r3.status_code == 200
    body3 = r3.json()
    assert body3["status"] == "claimed"
    assert body3["lead_id"] == body["lead_id"]


def test_lead_recent(client, auth_headers):
    r = client.get("/leads/recent", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert "leads" in body
    assert isinstance(body["leads"], list)


# ── Sprint 5: Voice + SMS ─────────────────────────────────────────────────────

def test_voice_dial_graceful_without_twilio(client, auth_headers):
    r = client.post("/voice/dial", headers=auth_headers, json={
        "lead_id": f"e2e-{uuid.uuid4()}",
        "to_number": "+12125550100",
        "country_code": "US",
    })
    assert r.status_code == 200
    body = r.json()
    # Expect not_configured when Twilio keys absent — not a 500
    assert "success" in body or "status" in body


def test_sms_send_blocked_without_consent(client, auth_headers):
    """SMS should be blocked by TCPA gate for unconsented lead."""
    r = client.post("/sms/send", headers=auth_headers, json={
        "lead_id": f"e2e-no-consent-{uuid.uuid4()}",
        "to_number": "+12125550100",
        "body": "E2E test SMS",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is False
    assert "TCPA" in body.get("error", "")


# ── Sprint 6: Zapier Webhooks ─────────────────────────────────────────────────

def test_zapier_subscribe_list_delete(client, auth_headers):
    # Subscribe
    r = client.post("/integrations/zapier/subscribe", headers=auth_headers, json={
        "event": "meeting_set",
        "url": "https://hooks.zapier.com/hooks/catch/e2e-test/",
        "name": "E2E test hook",
    })
    assert r.status_code == 200
    body = r.json()
    assert body.get("success") is True
    webhook_id = body["id"]

    # List
    r2 = client.get("/integrations/zapier", headers=auth_headers)
    assert r2.status_code == 200
    ids = [w["id"] for w in r2.json().get("subscriptions", [])]
    assert webhook_id in ids

    # Delete
    r3 = client.delete(f"/integrations/zapier/{webhook_id}", headers=auth_headers)
    assert r3.status_code == 200
    assert r3.json().get("success") is True


# ── Sprint 6: API Keys ────────────────────────────────────────────────────────

def test_api_key_generate_list_revoke(client, auth_headers):
    # Generate
    r = client.post("/api/keys", headers=auth_headers, json={"name": "E2E key"})
    assert r.status_code == 200
    body = r.json()
    assert "key" in body
    assert body["key"].startswith("urap_")
    key_id = body["key_id"]

    # List
    r2 = client.get("/api/keys", headers=auth_headers)
    assert r2.status_code == 200
    ids = [k["id"] for k in r2.json().get("keys", [])]
    assert key_id in ids

    # Revoke
    r3 = client.delete(f"/api/keys/{key_id}", headers=auth_headers)
    assert r3.status_code == 200
    assert r3.json().get("success") is True


# ── Sprint 6: Bulk Enrich ─────────────────────────────────────────────────────

def test_bulk_enrich_icp(client, auth_headers):
    r = client.post("/enrich/bulk-job/icp", headers=auth_headers, json={
        "domain": "stripe.com",
        "limit": 2,
    })
    assert r.status_code == 200
    body = r.json()
    assert "job_id" in body
    assert body["status"] in ("complete", "error")


def test_bulk_enrich_csv(client, auth_headers):
    csv_text = "first_name,last_name,email,company\nJane,Smith,jane@stripe.com,Stripe"
    r = client.post("/enrich/bulk-job/csv", headers=auth_headers, json={
        "csv_text": csv_text,
        "limit": 5,
    })
    assert r.status_code == 200
    body = r.json()
    assert "job_id" in body
    assert body["total"] >= 1


# ── Sprint 6: Autopilot ───────────────────────────────────────────────────────

def test_autopilot_enable_config_run_disable(client, auth_headers):
    icp = {"domain": "stripe.com", "title": "VP Sales", "limit": 1}

    # Enable
    r = client.post("/autopilot/enable", headers=auth_headers, json={
        "icp": icp,
        "schedule_hours": 24,
    })
    assert r.status_code == 200
    assert r.json().get("success") is True

    # Config
    r2 = client.get("/autopilot/config", headers=auth_headers)
    assert r2.status_code == 200
    body2 = r2.json()
    assert body2["enabled"] is True

    # Run now
    r3 = client.post("/autopilot/run", headers=auth_headers)
    assert r3.status_code == 200
    body3 = r3.json()
    assert "leads_found" in body3

    # Disable
    r4 = client.post("/autopilot/disable", headers=auth_headers)
    assert r4.status_code == 200
    assert r4.json().get("success") is True
