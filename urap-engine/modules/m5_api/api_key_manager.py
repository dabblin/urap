"""Tenant developer API key management — generate, list, revoke."""
import os
import secrets
import hashlib
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")

KEY_PREFIX = "urap_"
KEY_BYTES  = 32   # 256-bit key


def _db():
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def _hash(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


class ApiKeyManager:
    def generate(self, tenant_id: str, name: str = "Default") -> dict:
        """
        Generate a new API key for a tenant.
        The plaintext key is returned ONCE — only the SHA-256 hash is stored.
        Returns: {key, key_id, prefix, name}
        """
        raw = KEY_PREFIX + secrets.token_urlsafe(KEY_BYTES)
        key_hash = _hash(raw)
        prefix = raw[:12]   # "urap_" + first 7 chars — safe to display

        try:
            row = {
                "tenant_id": tenant_id,
                "name": name,
                "key_hash": key_hash,
                "key_prefix": prefix,
                "active": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            result = _db().table("urap_api_keys").insert(row).execute()
            key_id = result.data[0]["id"] if result.data else "unknown"
            return {"key": raw, "key_id": key_id, "prefix": prefix, "name": name}
        except Exception as exc:
            logger.error("[api_key_manager] generate error: %s", exc)
            return {"error": str(exc)}

    def validate(self, raw_key: str) -> dict | None:
        """
        Validate an incoming API key. Returns the tenant record or None.
        Updates last_used_at on success.
        """
        if not raw_key or not raw_key.startswith(KEY_PREFIX):
            return None
        key_hash = _hash(raw_key)
        try:
            result = (
                _db().table("urap_api_keys")
                .select("id,tenant_id,name,active")
                .eq("key_hash", key_hash)
                .eq("active", True)
                .limit(1)
                .execute()
            )
            if not result.data:
                return None
            record = result.data[0]
            # Fire-and-forget last_used update
            try:
                _db().table("urap_api_keys").update({
                    "last_used_at": datetime.now(timezone.utc).isoformat()
                }).eq("id", record["id"]).execute()
            except Exception:
                pass
            return record
        except Exception as exc:
            logger.error("[api_key_manager] validate error: %s", exc)
            return None

    def list_keys(self, tenant_id: str) -> list[dict]:
        """List all API keys for a tenant (prefix + metadata only — no hash exposed)."""
        try:
            result = (
                _db().table("urap_api_keys")
                .select("id,name,key_prefix,active,created_at,last_used_at")
                .eq("tenant_id", tenant_id)
                .order("created_at", desc=True)
                .execute()
            )
            return result.data or []
        except Exception as exc:
            logger.error("[api_key_manager] list_keys error: %s", exc)
            return []

    def revoke(self, key_id: str, tenant_id: str) -> dict:
        """Revoke (soft-delete) an API key."""
        try:
            _db().table("urap_api_keys").update({
                "active": False,
                "revoked_at": datetime.now(timezone.utc).isoformat(),
            }).eq("id", key_id).eq("tenant_id", tenant_id).execute()
            return {"success": True, "key_id": key_id}
        except Exception as exc:
            return {"success": False, "error": str(exc)}
