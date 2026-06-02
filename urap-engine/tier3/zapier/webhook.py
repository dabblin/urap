"""Zapier webhook dispatch — fires registered subscription URLs on globalStatus changes."""
import os
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")

DISPATCH_TIMEOUT = 5  # seconds per webhook call


def _db():
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def get_subscriptions(tenant_id: str, event: str) -> list[dict]:
    """Return active webhook subscriptions for a tenant + event."""
    try:
        result = (
            _db().table("urap_zapier_webhooks")
            .select("id,url,event")
            .eq("tenant_id", tenant_id)
            .eq("event", event)
            .eq("active", True)
            .execute()
        )
        return result.data or []
    except Exception as exc:
        logger.error("[zapier] get_subscriptions error: %s", exc)
        return []


def dispatch(
    tenant_id: str,
    event: str,
    payload: dict,
) -> list[dict]:
    """
    Fire all active webhook subscriptions for (tenant_id, event).
    Returns a list of dispatch results — one per subscription URL.
    Silent-fails per hook so one bad URL can't block others.
    """
    subs = get_subscriptions(tenant_id, event)
    if not subs:
        return []

    results = []
    for sub in subs:
        url = sub.get("url", "")
        if not url:
            continue
        try:
            resp = httpx.post(url, json={"event": event, "tenant_id": tenant_id, **payload}, timeout=DISPATCH_TIMEOUT)
            results.append({"id": sub["id"], "url": url, "status": resp.status_code, "ok": resp.is_success})
        except Exception as exc:
            logger.warning("[zapier] dispatch failed url=%s: %s", url, exc)
            results.append({"id": sub["id"], "url": url, "status": 0, "ok": False, "error": str(exc)})

    return results


def subscribe(tenant_id: str, event: str, url: str, name: str = "") -> dict:
    """Register a new Zapier webhook subscription."""
    try:
        row = {
            "tenant_id": tenant_id,
            "event": event,
            "url": url,
            "name": name or f"{event} webhook",
            "active": True,
        }
        result = _db().table("urap_zapier_webhooks").insert(row).execute()
        if result.data:
            return {"success": True, "id": result.data[0]["id"]}
        return {"success": False, "error": "Insert returned no data"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def unsubscribe(webhook_id: str, tenant_id: str) -> dict:
    """Remove a webhook subscription (hard delete — Zapier expects 200 on unsubscribe)."""
    try:
        _db().table("urap_zapier_webhooks").delete().eq("id", webhook_id).eq("tenant_id", tenant_id).execute()
        return {"success": True, "id": webhook_id}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def list_subscriptions(tenant_id: str) -> list[dict]:
    """List all webhook subscriptions for a tenant."""
    try:
        result = (
            _db().table("urap_zapier_webhooks")
            .select("id,event,url,name,active,created_at")
            .eq("tenant_id", tenant_id)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []
    except Exception as exc:
        logger.error("[zapier] list_subscriptions error: %s", exc)
        return []
