"""Stripe metered billing — report a qualified lead claim as a usage event."""
import os
import logging

logger = logging.getLogger(__name__)

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
# Subscription item ID for the metered "qualified leads" price.
# Set per-tenant via URAP_STRIPE_SUB_ITEM_ID env var or passed explicitly.
DEFAULT_SUB_ITEM_ID = os.getenv("URAP_STRIPE_SUB_ITEM_ID", "")


def report_lead_qualified(
    tenant_id: str,
    lead_id: str,
    subscription_item_id: str = "",
    quantity: int = 1,
) -> dict:
    """
    Fire a Stripe usage record for one qualified lead claim.
    Uses the metered billing pattern: stripe.subscription_items.create_usage_record().

    Returns: {success, usage_record_id, error}
    """
    if not STRIPE_SECRET_KEY:
        logger.warning("[stripe_metered] STRIPE_SECRET_KEY not set — skipping metered event")
        return {"success": False, "usage_record_id": "", "error": "STRIPE_SECRET_KEY not configured"}

    sub_item = subscription_item_id or DEFAULT_SUB_ITEM_ID
    if not sub_item:
        logger.warning("[stripe_metered] no subscription_item_id for tenant=%s — skipping", tenant_id)
        return {"success": False, "usage_record_id": "", "error": "URAP_STRIPE_SUB_ITEM_ID not configured"}

    try:
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY

        record = stripe.SubscriptionItem.create_usage_record(
            sub_item,
            quantity=quantity,
            action="increment",
            idempotency_key=f"urap-lead-{lead_id}",
        )
        logger.info("[stripe_metered] usage record created id=%s tenant=%s lead=%s", record.id, tenant_id, lead_id)
        return {"success": True, "usage_record_id": record.id, "error": ""}
    except Exception as exc:
        logger.error("[stripe_metered] error tenant=%s lead=%s: %s", tenant_id, lead_id, exc)
        return {"success": False, "usage_record_id": "", "error": str(exc)}
