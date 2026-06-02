"""
Drip sequence orchestrator — create templates, enroll contacts, fire due steps.

Sequence steps JSON shape (stored in urap_sequences.steps):
  [{"step": 0, "delay_days": 0, "subject": "...", "body_html": "..."},
   {"step": 1, "delay_days": 3, "subject": "...", "body_html": "..."},
   {"step": 2, "delay_days": 7, "subject": "...", "body_html": "..."}]

Enrollment lifecycle:
  active → completed  (all steps sent)
  active → replied    (Brevo webhook fires reply event)
  active → bounced    (Brevo webhook fires hard_bounce)
  active → unsubscribed
"""
from __future__ import annotations
import os
import uuid
from datetime import datetime, timezone, timedelta
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")


def _db():
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_KEY)


# ── Sequence CRUD ─────────────────────────────────────────────────────────────

async def create_sequence(
    tenant_id:  str,
    name:       str,
    from_email: str,
    from_name:  str,
    steps:      list[dict],
) -> dict:
    """
    Save a reusable sequence template.
    Returns: { sequence_id, name, step_count }
    """
    db = _db()
    seq_id = str(uuid.uuid4())
    db.table("urap_sequences").insert({
        "id":         seq_id,
        "tenant_id":  tenant_id,
        "name":       name,
        "from_email": from_email,
        "from_name":  from_name,
        "steps":      steps,
    }).execute()
    return {"sequence_id": seq_id, "name": name, "step_count": len(steps)}


async def get_sequences(tenant_id: str) -> list[dict]:
    """List all sequences for a tenant."""
    db = _db()
    resp = (
        db.table("urap_sequences")
        .select("id, name, from_email, from_name, steps, created_at")
        .eq("tenant_id", tenant_id)
        .order("created_at", desc=True)
        .execute()
    )
    return resp.data or []


# ── Enrollment ────────────────────────────────────────────────────────────────

async def enroll_contact(
    sequence_id: str,
    tenant_id:   str,
    to_email:    str,
    to_name:     str,
    company:     str = "",
) -> dict:
    """
    Enroll a contact in a sequence. Step 0 is due immediately (next_send_at = now).
    Returns: { enrollment_id, to_email, next_send_at }
    """
    db = _db()
    enroll_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    db.table("urap_sequence_enrollments").insert({
        "id":           enroll_id,
        "sequence_id":  sequence_id,
        "tenant_id":    tenant_id,
        "to_email":     to_email,
        "to_name":      to_name,
        "company":      company,
        "current_step": 0,
        "status":       "active",
        "next_send_at": now.isoformat(),
    }).execute()
    return {
        "enrollment_id": enroll_id,
        "to_email":      to_email,
        "next_send_at":  now.isoformat(),
    }


async def update_enrollment_status(enrollment_id: str, status: str) -> bool:
    """Update enrollment status — called by Brevo webhook on reply/bounce/unsub."""
    db = _db()
    db.table("urap_sequence_enrollments").update({
        "status":     status,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", enrollment_id).execute()
    return True


# ── Tick — fire due steps ─────────────────────────────────────────────────────

async def tick(max_send: int = 50) -> dict:
    """
    Find active enrollments whose next_send_at <= now, send the current step,
    then advance to the next step or mark completed.
    Called by the background loop every hour and by POST /outreach/sequence/tick.
    Returns: { sent, completed, errors }
    """
    from modules.m2_outreach.email_sequence import EmailSequenceService
    svc = EmailSequenceService()

    db = _db()
    now = datetime.now(timezone.utc).isoformat()

    due = (
        db.table("urap_sequence_enrollments")
        .select("id, sequence_id, tenant_id, to_email, to_name, company, current_step")
        .eq("status", "active")
        .lte("next_send_at", now)
        .limit(max_send)
        .execute()
    )
    enrollments = due.data or []
    if not enrollments:
        return {"sent": 0, "completed": 0, "errors": 0}

    seq_cache: dict[str, dict] = {}
    sent = completed = errors = 0

    for enr in enrollments:
        seq_id = enr["sequence_id"]
        if seq_id not in seq_cache:
            r = db.table("urap_sequences").select("*").eq("id", seq_id).execute()
            if r.data:
                seq_cache[seq_id] = r.data[0]

        seq = seq_cache.get(seq_id)
        if not seq:
            errors += 1
            continue

        steps: list[dict] = seq.get("steps") or []
        step_idx = enr["current_step"]

        if step_idx >= len(steps):
            db.table("urap_sequence_enrollments").update({
                "status": "completed",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }).eq("id", enr["id"]).execute()
            completed += 1
            continue

        step = steps[step_idx]
        result = await svc.send_single(
            lead_id=enr["id"],
            to_email=enr["to_email"],
            to_name=enr["to_name"],
            from_email=seq["from_email"],
            from_name=seq["from_name"],
            subject=step.get("subject", "(no subject)"),
            body_html=step.get("body_html", ""),
            tag=enr["id"],  # enrollment_id as Brevo tag for webhook correlation
        )

        if result.success:
            next_step = step_idx + 1
            if next_step >= len(steps):
                db.table("urap_sequence_enrollments").update({
                    "current_step": next_step,
                    "status":       "completed",
                    "updated_at":   datetime.now(timezone.utc).isoformat(),
                }).eq("id", enr["id"]).execute()
                completed += 1
            else:
                next_delay = steps[next_step].get("delay_days", 1)
                next_send = datetime.now(timezone.utc) + timedelta(days=next_delay)
                db.table("urap_sequence_enrollments").update({
                    "current_step": next_step,
                    "next_send_at": next_send.isoformat(),
                    "updated_at":   datetime.now(timezone.utc).isoformat(),
                }).eq("id", enr["id"]).execute()
            sent += 1
        else:
            errors += 1

    return {"sent": sent, "completed": completed, "errors": errors}
