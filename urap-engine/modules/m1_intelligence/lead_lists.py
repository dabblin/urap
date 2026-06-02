"""
Lead list management — saves search results + enriched contacts to Supabase.

Tables auto-created on first write via Supabase SQL:
  urap_lead_lists      — named list metadata (tenant_id, name, item_count)
  urap_lead_list_items — individual companies per list (FK → urap_lead_lists)
"""
from __future__ import annotations
import os
import uuid
from datetime import datetime, timezone

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")


def _db():
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_KEY)


async def save_list(tenant_id: str, name: str, items: list[dict]) -> dict:
    """
    Create a named lead list and insert all items.
    Each item dict may contain: name, domain, website, phone, email,
    contact_name, contact_title, industry, location, source.
    Returns: { list_id, name, count, created_at }
    """
    db = _db()
    list_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    db.table("urap_lead_lists").insert({
        "id": list_id,
        "tenant_id": tenant_id,
        "name": name,
        "item_count": len(items),
        "created_at": now,
    }).execute()

    rows = [
        {
            "list_id":       list_id,
            "tenant_id":     tenant_id,
            "company_name":  item.get("name", ""),
            "domain":        item.get("domain", ""),
            "website":       item.get("website", ""),
            "phone":         item.get("phone", ""),
            "email":         item.get("email", ""),
            "contact_name":  item.get("contact_name", ""),
            "contact_title": item.get("contact_title", ""),
            "industry":      item.get("industry", ""),
            "location":      item.get("location", ""),
            "source":        item.get("source", ""),
        }
        for item in items
    ]

    for i in range(0, len(rows), 50):
        db.table("urap_lead_list_items").insert(rows[i : i + 50]).execute()

    return {"list_id": list_id, "name": name, "count": len(items), "created_at": now}


async def get_lists(tenant_id: str) -> list[dict]:
    """Return all lists for a tenant, most recent first."""
    db = _db()
    resp = (
        db.table("urap_lead_lists")
        .select("id, name, item_count, created_at")
        .eq("tenant_id", tenant_id)
        .order("created_at", desc=True)
        .execute()
    )
    return resp.data or []


async def get_list_items(list_id: str, tenant_id: str) -> list[dict]:
    """Return all items in a specific list."""
    db = _db()
    resp = (
        db.table("urap_lead_list_items")
        .select("id, company_name, domain, phone, email, contact_name, contact_title, industry, location, source")
        .eq("list_id", list_id)
        .eq("tenant_id", tenant_id)
        .execute()
    )
    return resp.data or []


async def delete_list(list_id: str, tenant_id: str) -> bool:
    """Delete a list (items cascade via FK in Supabase)."""
    db = _db()
    db.table("urap_lead_lists").delete().eq("id", list_id).eq("tenant_id", tenant_id).execute()
    return True
