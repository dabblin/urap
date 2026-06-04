"""Module II — Campaign dispatcher with AI personalization.

Batch-sends a campaign to all contacts in a saved list.
If ai_personalize=True, calls Claude Haiku to write a custom opening sentence per lead.
Merge vars: {{name}}, {{first_name}}, {{company}}, {{title}}, {{personalized_opener}}
"""
import os
import asyncio
import uuid
import json
from typing import Optional
import httpx

HAIKU_URL = "https://api.anthropic.com/v1/messages"
HAIKU_MODEL = "claude-haiku-4-5-20251001"
_OPENER_BATCH = 10   # parallel Haiku calls per batch


def _render(template: str, lead: dict, opener: str = "") -> str:
    first = (lead.get("name") or "").split()[0] if lead.get("name") else ""
    out = template
    out = out.replace("{{name}}", lead.get("name") or "")
    out = out.replace("{{first_name}}", first)
    out = out.replace("{{company}}", lead.get("company") or "")
    out = out.replace("{{title}}", lead.get("title") or "")
    out = out.replace("{{personalized_opener}}", opener)
    return out


async def _haiku_opener(lead: dict, api_key: str, client: httpx.AsyncClient) -> str:
    name    = lead.get("name") or "there"
    title   = lead.get("title") or ""
    company = lead.get("company") or ""

    who = name
    if title:
        who += f", {title}"
    if company:
        who += f" at {company}"

    prompt = (
        f"Write one short, natural-sounding opening sentence for a cold email to {who}. "
        "Reference their role or company in a genuinely relevant way. "
        "No filler phrases. No exclamation marks. Output only the sentence."
    )
    try:
        resp = await client.post(
            HAIKU_URL,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": HAIKU_MODEL,
                "max_tokens": 80,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=15,
        )
        if resp.status_code == 200:
            return resp.json()["content"][0]["text"].strip()
    except Exception:
        pass
    return ""


async def dispatch(
    *,
    campaign: dict,
    contacts: list[dict],
    tenant_id: str,
    email_svc,   # EmailSequenceService
    db,          # Supabase client
) -> dict:
    """Dispatch campaign to all contacts. Returns {sent, failed, skipped}."""
    api_key       = os.environ.get("ANTHROPIC_API_KEY", "")
    ai_personalize = campaign.get("ai_personalize", False)
    campaign_id   = campaign["id"]
    subject_tpl   = campaign.get("subject_template", "")
    body_tpl      = campaign.get("body_template", "")
    from_email    = campaign.get("from_email", "")
    from_name     = campaign.get("from_name", "") or ""

    # ── 1. Generate personalized openers in parallel batches ─────────────────
    openers: list[str] = [""] * len(contacts)
    if ai_personalize and api_key:
        async with httpx.AsyncClient() as client:
            for i in range(0, len(contacts), _OPENER_BATCH):
                batch   = contacts[i : i + _OPENER_BATCH]
                results = await asyncio.gather(
                    *[_haiku_opener(c, api_key, client) for c in batch],
                    return_exceptions=True,
                )
                for j, r in enumerate(results):
                    openers[i + j] = r if isinstance(r, str) else ""

    # ── 2. Send each contact ──────────────────────────────────────────────────
    sent = failed = skipped = 0
    send_records: list[dict] = []

    for idx, contact in enumerate(contacts):
        email = (contact.get("email") or "").strip()
        if not email:
            skipped += 1
            continue

        opener    = openers[idx]
        subject   = _render(subject_tpl, contact, opener)
        body_html = _render(body_tpl, contact, opener)
        lead_id   = contact.get("lead_id") or str(uuid.uuid4())

        result = await email_svc.send_single(
            lead_id=lead_id,
            to_email=email,
            to_name=contact.get("name") or "",
            from_email=from_email,
            from_name=from_name,
            subject=subject,
            body_html=body_html,
            require_consent=False,
            tag=f"campaign:{campaign_id}",
        )

        send_records.append({
            "id":          str(uuid.uuid4()),
            "campaign_id": campaign_id,
            "tenant_id":   tenant_id,
            "lead_id":     lead_id,
            "to_email":    email,
            "subject":     subject,
            "status":      "sent" if result.success else "failed",
            "provider":    result.provider,
            "error":       result.error,
        })

        if result.success:
            sent += 1
        else:
            failed += 1

    # ── 3. Persist results ───────────────────────────────────────────────────
    try:
        if send_records:
            db.table("urap_campaign_sends").insert(send_records).execute()
        db.table("urap_campaigns").update({
            "status":       "sent",
            "sent_count":   sent,
            "failed_count": failed,
        }).eq("id", campaign_id).execute()
    except Exception:
        pass

    return {"sent": sent, "failed": failed, "skipped": skipped}


async def dispatch_stream(
    *,
    campaign: dict,
    contacts: list[dict],
    tenant_id: str,
    email_svc,   # EmailSequenceService
    db,          # Supabase client
):
    """Dispatch campaign to all contacts and yield progress events as NDJSON."""
    api_key       = os.environ.get("ANTHROPIC_API_KEY", "")
    ai_personalize = campaign.get("ai_personalize", False)
    campaign_id   = campaign["id"]
    subject_tpl   = campaign.get("subject_template", "")
    body_tpl      = campaign.get("body_template", "")
    from_email    = campaign.get("from_email", "")
    from_name     = campaign.get("from_name", "") or ""

    yield json.dumps({"event": "start", "total": len(contacts)}) + "\n"

    # ── 1. Generate personalized openers in parallel batches ─────────────────
    openers: list[str] = [""] * len(contacts)
    if ai_personalize and api_key:
        yield json.dumps({"event": "status", "message": "Analyzing leads and generating AI personalized openers..."}) + "\n"
        async with httpx.AsyncClient() as client:
            for i in range(0, len(contacts), _OPENER_BATCH):
                batch   = contacts[i : i + _OPENER_BATCH]
                yield json.dumps({"event": "status", "message": f"Personalizing leads {i+1} to {min(i+_OPENER_BATCH, len(contacts))}..."}) + "\n"
                results = await asyncio.gather(
                    *[_haiku_opener(c, api_key, client) for c in batch],
                    return_exceptions=True,
                )
                for j, r in enumerate(results):
                    openers[i + j] = r if isinstance(r, str) else ""

    # ── 2. Send each contact ──────────────────────────────────────────────────
    sent = failed = skipped = 0
    send_records: list[dict] = []

    for idx, contact in enumerate(contacts):
        email = (contact.get("email") or "").strip()
        name = contact.get("name") or "there"
        if not email:
            skipped += 1
            yield json.dumps({"event": "skipped", "email": "(no email)", "name": name, "reason": "Missing email address"}) + "\n"
            continue

        yield json.dumps({"event": "sending", "email": email, "name": name}) + "\n"

        opener    = openers[idx]
        subject   = _render(subject_tpl, contact, opener)
        body_html = _render(body_tpl, contact, opener)
        lead_id   = contact.get("lead_id") or str(uuid.uuid4())

        result = await email_svc.send_single(
            lead_id=lead_id,
            to_email=email,
            to_name=contact.get("name") or "",
            from_email=from_email,
            from_name=from_name,
            subject=subject,
            body_html=body_html,
            require_consent=False,
            tag=f"campaign:{campaign_id}",
        )

        send_records.append({
            "id":          str(uuid.uuid4()),
            "campaign_id": campaign_id,
            "tenant_id":   tenant_id,
            "lead_id":     lead_id,
            "to_email":    email,
            "subject":     subject,
            "status":      "sent" if result.success else "failed",
            "provider":    result.provider,
            "error":       result.error,
        })

        if result.success:
            sent += 1
            yield json.dumps({"event": "sent", "email": email, "name": name}) + "\n"
        else:
            failed += 1
            yield json.dumps({"event": "failed", "email": email, "name": name, "error": result.error or "Delivery failed"}) + "\n"

    # ── 3. Persist results ───────────────────────────────────────────────────
    yield json.dumps({"event": "status", "message": "Saving campaign progress to database..."}) + "\n"
    try:
        if send_records:
            db.table("urap_campaign_sends").insert(send_records).execute()
        db.table("urap_campaigns").update({
            "status":       "sent",
            "sent_count":   sent,
            "failed_count": failed,
        }).eq("id", campaign_id).execute()
    except Exception as exc:
        yield json.dumps({"event": "status", "message": f"Database update error: {str(exc)}"}) + "\n"

    yield json.dumps({"event": "complete", "sent": sent, "failed": failed, "skipped": skipped}) + "\n"
