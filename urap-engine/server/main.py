"""urap-engine — URAP FastAPI microservice (mirrors dabblin-voice architecture)"""
import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

from fastapi import FastAPI, Request, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn

from server.middleware import require_api_key
from modules.m1_intelligence.enrichment import EnrichmentService
from modules.m6_compliance.consent_ledger import ConsentLedgerService
from modules.m2_outreach.channel_state_machine import ChannelStateMachine
from modules.m2_outreach.email_sequence import EmailSequenceService
from modules.m3_agents.warp_mode import WarpModeAgent
from modules.m3_agents.reply_intelligence import ReplyIntelligenceAgent
from modules.m4_inbound.lead_router import LeadRouterService
from modules.m5_api.api_key_manager import ApiKeyManager
from modules.m5_api.bulk_enrich_runner import BulkEnrichRunner
from modules.m5_api.autopilot_runner import AutopilotRunner
from modules.m4_inbound.marketplace_router import MarketplaceRouter
from modules.m4_inbound.race_agents import RaceAuction
from modules.m1_intelligence.company_search import search_companies

app = FastAPI(title="URAP Engine", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("URAP_ALLOWED_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

_enrichment = EnrichmentService()
_consent = ConsentLedgerService()
_csm = ChannelStateMachine()
_email_svc = EmailSequenceService()
_warp = WarpModeAgent()
_reply_intel = ReplyIntelligenceAgent()
_lead_router = LeadRouterService()
_api_keys = ApiKeyManager()
_bulk_enrich = BulkEnrichRunner()
_autopilot = AutopilotRunner()
_marketplace = MarketplaceRouter()
_race = RaceAuction()


# ── Request models ────────────────────────────────────────────────────────────

class EnrichRequest(BaseModel):
    domain: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    title: Optional[str] = None


class BulkEnrichRequest(BaseModel):
    domain: str
    limit: int = 25


class ConsentRecordRequest(BaseModel):
    lead_id: str
    tenant_id: str
    source: str           # TrustedForm cert URL
    ip_address: str
    platform_name: str
    one_to_one_rule: bool = True


class ConsentCheckRequest(BaseModel):
    lead_id: str


class EmailSendRequest(BaseModel):
    lead_id: str
    to_email: str
    to_name: str
    from_email: str
    from_name: str
    subject: str
    body_html: str
    require_consent: bool = False


class ChannelEventRequest(BaseModel):
    lead_id: str
    channel: str
    event: str   # reply | send | open | bounce | unsubscribe | meeting_set


class IntentScoreRequest(BaseModel):
    domain: Optional[str] = None
    limit: int = 25


class WarpRunRequest(BaseModel):
    title: Optional[str] = None
    domain: str
    industry: Optional[str] = None
    value_prop: Optional[str] = None
    icp_label: Optional[str] = None
    limit: int = 10


class ReplyParseRequest(BaseModel):
    lead_id: str
    channel: str    # email | sms | linkedin | voice
    reply_text: str


class LeadCaptureRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    source: str = "web"
    raw: Optional[dict] = None


class LeadClaimRequest(BaseModel):
    preview_id: str


class DialRequest(BaseModel):
    lead_id: str
    to_number: str
    country_code: str = "US"
    status_callback_url: Optional[str] = None


class SmsRequest(BaseModel):
    lead_id: str
    to_number: str
    body: str
    country_code: str = "US"


class ZapierSubscribeRequest(BaseModel):
    event: str      # globalStatus value: engaged | interested | meeting_set | qualified | etc.
    url: str
    name: Optional[str] = None


class ApiKeyCreateRequest(BaseModel):
    name: str = "Default"


class BulkEnrichCsvRequest(BaseModel):
    csv_text: str
    limit: int = 100


class BulkEnrichIcpRequest(BaseModel):
    domain: str
    limit: int = 50


class AutopilotConfigRequest(BaseModel):
    icp: dict
    schedule_hours: int = 24
    route_after_warp: bool = False
    route_marketplace_id: Optional[str] = None
    route_min_score: int = 60


class MarketplaceConfigRequest(BaseModel):
    webhook_url: str
    api_key: Optional[str] = None
    cpl: float = 0.0


class WebhookTestRequest(BaseModel):
    webhook_url: str
    api_key: Optional[str] = None


class RouteDispatchRequest(BaseModel):
    marketplace_id: str = ""
    leads: list[dict]
    ping_post: bool = False


class RaceDispatchRequest(BaseModel):
    leads: list[dict]
    timeout: float = 5.0


class CompanySearchRequest(BaseModel):
    domain:   Optional[str] = None
    name:     Optional[str] = None
    keywords: Optional[str] = None
    location: Optional[str] = None
    industry: Optional[str] = None
    limit:    int = 25


class CompanyContactRequest(BaseModel):
    name:    Optional[str] = None
    domain:  Optional[str] = None
    website: Optional[str] = None
    phone:   Optional[str] = None
    yelp_id: Optional[str] = None


class CompanyContactBatchItem(BaseModel):
    index:   int
    name:    Optional[str] = None
    domain:  Optional[str] = None
    website: Optional[str] = None
    phone:   Optional[str] = None
    yelp_id: Optional[str] = None


class CompanyContactBatchRequest(BaseModel):
    companies:    list[CompanyContactBatchItem]
    max_parallel: int = 5


class SequenceStep(BaseModel):
    step:       int
    delay_days: int = 0
    subject:    str
    body_html:  str


class RunIcpAutopilotRequest(BaseModel):
    keywords:    str = ""
    location:    str = ""
    industry:    str = ""
    limit:       int = 25
    sequence_id: str


class CreateSequenceRequest(BaseModel):
    name:       str
    from_email: str
    from_name:  str
    steps:      list[SequenceStep]


class EnrollContactRequest(BaseModel):
    sequence_id: str
    to_email:    str
    to_name:     str  = ""
    company:     str  = ""


class SaveListItem(BaseModel):
    name:          Optional[str] = None
    domain:        Optional[str] = None
    website:       Optional[str] = None
    phone:         Optional[str] = None
    email:         Optional[str] = None
    contact_name:  Optional[str] = None
    contact_title: Optional[str] = None
    industry:      Optional[str] = None
    location:      Optional[str] = None
    source:        Optional[str] = None


class SaveListRequest(BaseModel):
    name:  str
    items: list[SaveListItem]


# ── Sprint 9A — Campaign Lists + Campaigns ────────────────────────────────────

class CampaignListContact(BaseModel):
    lead_id:           Optional[str] = None
    name:              str = ""
    title:             str = ""
    company:           str = ""
    email:             str
    phone:             Optional[str] = None
    email_verified:    bool = False
    enrichment_source: str = ""


class CampaignListSaveRequest(BaseModel):
    name:     str
    contacts: list[CampaignListContact]


class CampaignCreateRequest(BaseModel):
    name:             str
    list_id:          str
    from_email:       str
    from_name:        str = ""
    subject_template: str
    body_template:    str
    ai_personalize:   bool = False


class GenerateTemplatesRequest(BaseModel):
    list_id:          str


class CampaignPageCreateRequest(BaseModel):
    slug:         str
    headline:     str
    subheadline:  str = ""
    cta_text:     str = "Get Started"
    brand_color:  str = "#6366f1"
    form_fields:  list[str] = ["name", "email", "phone"]
    logo_url:     Optional[str] = None
    company_name: Optional[str] = None
    campaign_id:  Optional[str] = None


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "service": "urap-engine", "version": "0.1.0"}


# ── Sprint 1 — Module I: Enrichment ──────────────────────────────────────────

@app.post("/enrich", dependencies=[Depends(require_api_key)])
async def enrich_contact(body: EnrichRequest, x_tenant_id: str = Header(...)):
    contact = await _enrichment.enrich_contact(
        tenant_id=x_tenant_id,
        first_name=body.first_name,
        last_name=body.last_name,
        domain=body.domain,
        title=body.title,
    )
    return {"contacts": [contact] if contact else []}


@app.post("/enrich/bulk", dependencies=[Depends(require_api_key)])
async def bulk_enrich(body: BulkEnrichRequest, x_tenant_id: str = Header(...)):
    contacts = await _enrichment.bulk_enrich_domain(
        tenant_id=x_tenant_id,
        domain=body.domain,
        limit=min(body.limit, 50),
    )
    return {"contacts": contacts, "count": len(contacts)}


@app.post("/companies/contact", dependencies=[Depends(require_api_key)])
async def company_contact(body: CompanyContactRequest, x_tenant_id: str = Header(...)):
    """Discover contact email + name for a single business via Hunter → website scrape."""
    from modules.m1_intelligence.contact_discover import discover_contact
    return await discover_contact(
        name=body.name or "",
        domain=body.domain or "",
        website=body.website or "",
        phone=body.phone or "",
        yelp_id=body.yelp_id or "",
    )


@app.post("/companies/contact/batch", dependencies=[Depends(require_api_key)])
async def company_contact_batch(body: CompanyContactBatchRequest, x_tenant_id: str = Header(...)):
    """Discover contact info for up to 50 businesses in parallel (semaphore-limited)."""
    from modules.m1_intelligence.contact_discover import discover_contacts_batch
    results = await discover_contacts_batch(
        companies=[c.model_dump() for c in body.companies],
        max_parallel=min(body.max_parallel, 10),
    )
    return {"results": results, "count": len(results)}


# ── Sprint B — List Management ────────────────────────────────────────────────

@app.post("/companies/list/save", dependencies=[Depends(require_api_key)])
async def save_lead_list(body: SaveListRequest, x_tenant_id: str = Header(...)):
    """Save a named lead list (results + enriched contacts) to Supabase."""
    from modules.m1_intelligence.lead_lists import save_list
    result = await save_list(
        tenant_id=x_tenant_id,
        name=body.name.strip(),
        items=[i.model_dump() for i in body.items],
    )
    return result


@app.get("/companies/lists", dependencies=[Depends(require_api_key)])
async def get_lead_lists(x_tenant_id: str = Header(...)):
    """Return all saved lists for the tenant, most recent first."""
    from modules.m1_intelligence.lead_lists import get_lists
    lists = await get_lists(tenant_id=x_tenant_id)
    return {"lists": lists, "count": len(lists)}


@app.get("/companies/list/{list_id}", dependencies=[Depends(require_api_key)])
async def get_lead_list_items(list_id: str, x_tenant_id: str = Header(...)):
    """Return all companies in a saved list."""
    from modules.m1_intelligence.lead_lists import get_list_items
    items = await get_list_items(list_id=list_id, tenant_id=x_tenant_id)
    return {"items": items, "count": len(items)}


@app.delete("/companies/list/{list_id}", dependencies=[Depends(require_api_key)])
async def delete_lead_list(list_id: str, x_tenant_id: str = Header(...)):
    """Delete a saved list and all its items."""
    from modules.m1_intelligence.lead_lists import delete_list
    await delete_list(list_id=list_id, tenant_id=x_tenant_id)
    return {"deleted": True, "list_id": list_id}


@app.post("/companies/search", dependencies=[Depends(require_api_key)])
async def company_search(body: CompanySearchRequest, x_tenant_id: str = Header(...)):
    """
    Two modes:
    - domain provided → Hunter.io/Snov.io enrichment (single company, rich metadata)
    - keywords/location/industry → Apollo.io discovery (list of matching companies)
    """
    companies = await search_companies(
        domain=body.domain or "",
        name=body.name or "",
        keywords=body.keywords or "",
        location=body.location or "",
        industry=body.industry or "",
        limit=min(body.limit, 100),
    )
    return {"companies": companies, "count": len(companies)}


# ── Sprint 2 — Module VI: TCPA Consent Ledger ────────────────────────────────

@app.post("/consent/record")
async def record_consent(body: ConsentRecordRequest, request: Request):
    """Record a TrustedForm consent certificate. Public — no API key required.
    Called by the lead capture form after TrustedForm populates the cert URL.
    """
    try:
        record = _consent.record_consent(
            tenant_id=body.tenant_id,
            lead_id=body.lead_id,
            source=body.source,
            ip_address=request.client.host if request.client else body.ip_address,
            platform_name=body.platform_name,
            one_to_one_rule=body.one_to_one_rule,
        )
        return {"status": "recorded", "id": record["id"]}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@app.post("/consent/check", dependencies=[Depends(require_api_key)])
async def check_consent(body: ConsentCheckRequest, x_tenant_id: str = Header(...)):
    """TCPA gate check — returns consented=True only if a cert record exists.
    Outreach orchestrator MUST call this before queuing any SMS, voice, or
    cold-email sequence for a lead.
    """
    consented = _consent.check_tcpa_gate(body.lead_id)
    record = _consent.get_latest_consent(body.lead_id) if consented else None
    return {
        "lead_id": body.lead_id,
        "consented": consented,
        "record": record,
    }


# ── Sprint 3 — Module II: Outreach Engine ────────────────────────────────────

@app.post("/outreach/email/send", dependencies=[Depends(require_api_key)])
async def send_email(body: EmailSendRequest, x_tenant_id: str = Header(...)):
    """Send a single email through the SMTP2GO → Brevo → Mailgun waterfall."""
    result = await _email_svc.send_single(
        lead_id=body.lead_id,
        to_email=body.to_email,
        to_name=body.to_name,
        from_email=body.from_email,
        from_name=body.from_name,
        subject=body.subject,
        body_html=body.body_html,
        require_consent=body.require_consent,
    )
    return {
        "success": result.success,
        "provider": result.provider,
        "message_id": result.message_id,
        "error": result.error,
    }


@app.post("/outreach/channel/event", dependencies=[Depends(require_api_key)])
async def channel_event(body: ChannelEventRequest, x_tenant_id: str = Header(...)):
    """Update lead channel state. Called by webhooks, reply parsers, and dialer callbacks."""
    handlers = {
        "reply": lambda: _csm.handle_reply(body.lead_id, body.channel),
        "send": lambda: _csm.handle_send(body.lead_id, body.channel),
        "open": lambda: _csm.handle_open(body.lead_id),
        "bounce": lambda: _csm.handle_bounce(body.lead_id),
        "unsubscribe": lambda: _csm.handle_unsubscribe(body.lead_id),
        "meeting_set": lambda: _csm.handle_meeting_set(body.lead_id),
    }
    handler = handlers.get(body.event)
    if not handler:
        return {"error": f"Unknown event: {body.event}"}
    result = handler()
    # Zapier dispatch — fire any registered webhooks for the new globalStatus
    new_status = (result or {}).get("global_status")
    if new_status:
        try:
            from tier3.zapier.webhook import dispatch
            dispatch(
                tenant_id=x_tenant_id,
                event=new_status,
                payload={"lead_id": body.lead_id, "channel": body.channel, "trigger_event": body.event},
            )
        except Exception:
            pass  # never let Zapier dispatch block the response
    return result


@app.post("/outreach/intent/score", dependencies=[Depends(require_api_key)])
async def score_intent(body: IntentScoreRequest, x_tenant_id: str = Header(...)):
    """Return intent-scored contacts from Supabase cache, sorted by score desc.
    Full 3rd-party intent signals ship Sprint 4. This sprint: enrichment-signal scoring.
    """
    try:
        from supabase import create_client
        import random
        db = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"])
        query = db.table("urap_contacts").select("*").eq("tenant_id", x_tenant_id)
        if body.domain:
            query = query.eq("company", body.domain)
        result = query.limit(body.limit).execute()
        contacts = result.data or []
        
        # Sprint 4: Inject mock 3rd-party intent signals
        possible_signals = ["G2: Pricing Page", "Bombora: High Intent", "Job Change: New VP", "Tech Install: Stripe", "Site Visit: 3x"]
        
        for c in contacts:
            if not c.get("intent_signals"):
                # Assign 0-2 random signals for demo purposes
                c["intent_signals"] = random.sample(possible_signals, random.randint(0, 2))
                
        scored = sorted(
            [{"score": _email_svc.score_intent(c) + (len(c["intent_signals"]) * 10), **c} for c in contacts],
            key=lambda x: x["score"],
            reverse=True,
        )
        return {"contacts": scored, "count": len(scored)}
    except Exception as exc:
        return {"contacts": [], "count": 0, "error": str(exc)}


# ── Sprint 4 — Module III: AI Sales Agents ───────────────────────────────────

@app.post("/agents/warp/run", dependencies=[Depends(require_api_key)])
async def warp_run(body: WarpRunRequest, x_tenant_id: str = Header(...)):
    """Launch a Warp Mode job: ICP → enrich → AI copy → queue.
    Gemini Flash drafts, Claude Sonnet reviews. Falls back to template if keys absent.
    """
    icp = {
        "title": body.title or "",
        "domain": body.domain,
        "industry": body.industry or "",
        "value_prop": body.value_prop or "AI-powered revenue acceleration",
        "icp_label": body.icp_label or f"{body.title or 'ICP'} @ {body.domain}",
        "limit": body.limit,
    }
    result = await _warp.run_job(icp=icp, tenant_id=x_tenant_id)
    return {
        "job_id": result.job_id,
        "icp_label": result.icp_label,
        "leads_found": result.leads_found,
        "sequences_queued": result.sequences_queued,
        "generated": result.generated,
        "error": result.error,
    }


@app.get("/agents/warp/jobs", dependencies=[Depends(require_api_key)])
async def warp_jobs(x_tenant_id: str = Header(...), limit: int = 10):
    """List recent Warp Mode jobs for this tenant."""
    jobs = _warp.list_jobs(tenant_id=x_tenant_id, limit=min(limit, 25))
    return {"jobs": jobs, "count": len(jobs)}


@app.post("/agents/reply/parse", dependencies=[Depends(require_api_key)])
async def reply_parse(body: ReplyParseRequest, x_tenant_id: str = Header(...)):
    """Parse an incoming reply: classify sentiment, update channel state, fire alerts."""
    result = await _reply_intel.parse_reply(
        lead_id=body.lead_id,
        channel=body.channel,
        reply_text=body.reply_text,
        tenant_id=x_tenant_id,
    )
    return {
        "lead_id": result.lead_id,
        "channel": result.channel,
        "sentiment": result.sentiment,
        "confidence": result.confidence,
        "global_status_updated_to": result.global_status_updated_to,
        "calendar_link": result.calendar_link,
        "telegram_sent": result.telegram_sent,
        "summary": result.summary,
    }


# ── Sprint 5 — Module IV: Inbound Lead Capture & Distribution ─────────────────

@app.post("/leads/capture")
async def capture_lead(
    body: LeadCaptureRequest,
    request: Request,
    x_tenant_id: str = Header(...),
):
    """
    Step 1 — Inbound lead capture. Enriches, geo-locates, stores in urap_lead_distribution.
    Public — no API key required (called by embed snippet on client websites).
    """
    lead = await _lead_router.capture(
        tenant_id=x_tenant_id,
        first_name=body.first_name or "",
        last_name=body.last_name or "",
        email=body.email or "",
        phone=body.phone or "",
        company=body.company or "",
        title=body.title or "",
        ip_address=request.client.host if request.client else "",
        source=body.source,
        raw=body.raw,
    )
    preview = _lead_router.preview(lead)
    return {
        "status": "captured",
        "lead_id": lead.lead_id,
        "preview_id": preview.preview_id,
        "attributes": {
            "company_size": preview.company_size,
            "industry": preview.industry,
            "title_level": preview.title_level,
            "intent_count": preview.intent_count,
            "country_code": preview.country_code,
        },
        "expires_at": preview.expires_at,
    }


@app.get("/leads/preview/{preview_id}", dependencies=[Depends(require_api_key)])
async def get_lead_preview(preview_id: str, x_tenant_id: str = Header(...)):
    """
    Step 2 — Ping-post preview. Returns anonymized attributes for buyer evaluation.
    Called by potential buyers before committing to a claim.
    """
    cached = _lead_router._preview_cache.get(preview_id)
    if not cached:
        return {"error": "Preview not found or expired", "preview_id": preview_id}
    return {"preview_id": preview_id, "status": "available", "expires_at": cached["expires_at"]}


@app.post("/leads/claim", dependencies=[Depends(require_api_key)])
async def claim_lead(body: LeadClaimRequest, x_tenant_id: str = Header(...)):
    """
    Step 3 — Ping-post claim. Releases full PII to buyer, fires Stripe metered event.
    Buyer is charged per qualified lead claimed.
    """
    result = await _lead_router.claim(
        preview_id=body.preview_id,
        buyer_tenant_id=x_tenant_id,
    )
    if not result.success:
        return {"status": "error", "error": result.error, "preview_id": body.preview_id}

    pii = _lead_router.get_lead_pii(result.lead_id)
    return {
        "status": "claimed",
        "lead_id": result.lead_id,
        "preview_id": body.preview_id,
        "stripe_event_fired": result.stripe_event_fired,
        "lead": pii,
    }


@app.get("/leads/recent", dependencies=[Depends(require_api_key)])
async def recent_leads(x_tenant_id: str = Header(...), limit: int = 20):
    """List recently captured leads for this tenant (no PII in listing)."""
    leads = _lead_router.list_recent(tenant_id=x_tenant_id, limit=min(limit, 50))
    return {"leads": leads, "count": len(leads)}


# ── Sprint 5 — Voice + SMS (Twilio Power Dialer) ──────────────────────────────

@app.post("/voice/dial", dependencies=[Depends(require_api_key)])
async def voice_dial(body: DialRequest, x_tenant_id: str = Header(...)):
    """Initiate outbound call from the URAP power dialer."""
    from tier3.twilio.client import dial_lead
    result = dial_lead(
        to_number=body.to_number,
        lead_id=body.lead_id,
        country_code=body.country_code,
        status_callback_url=body.status_callback_url or "",
    )
    if result["success"]:
        _csm.handle_send(body.lead_id, "voice")
    return result


@app.get("/voice/status/{call_sid}", dependencies=[Depends(require_api_key)])
async def voice_status(call_sid: str, x_tenant_id: str = Header(...)):
    """Get current status of an active call."""
    from tier3.twilio.client import get_call_status
    return get_call_status(call_sid)


@app.post("/voice/hangup/{call_sid}", dependencies=[Depends(require_api_key)])
async def voice_hangup(call_sid: str, x_tenant_id: str = Header(...)):
    """Hang up an active call."""
    from tier3.twilio.client import end_call
    return end_call(call_sid)


@app.post("/sms/send", dependencies=[Depends(require_api_key)])
async def sms_send(body: SmsRequest, x_tenant_id: str = Header(...)):
    """Send outbound SMS. TCPA consent must be verified by caller before use."""
    consented = _consent.check_tcpa_gate(body.lead_id)
    if not consented:
        return {
            "success": False,
            "error": "TCPA gate: no consent record for this lead",
            "lead_id": body.lead_id,
        }
    from tier3.twilio.client import send_sms
    result = send_sms(
        to_number=body.to_number,
        body=body.body,
        lead_id=body.lead_id,
        country_code=body.country_code,
    )
    if result["success"]:
        _csm.handle_send(body.lead_id, "sms")
    return result


# ── Sprint 6 — Zapier Integrations ───────────────────────────────────────────

@app.post("/integrations/zapier/subscribe", dependencies=[Depends(require_api_key)])
async def zapier_subscribe(body: ZapierSubscribeRequest, x_tenant_id: str = Header(...)):
    """Register a Zapier webhook for a globalStatus event."""
    from tier3.zapier.webhook import subscribe
    result = subscribe(tenant_id=x_tenant_id, event=body.event, url=body.url, name=body.name or "")
    return result


@app.delete("/integrations/zapier/{webhook_id}", dependencies=[Depends(require_api_key)])
async def zapier_unsubscribe(webhook_id: str, x_tenant_id: str = Header(...)):
    """Remove a Zapier webhook subscription."""
    from tier3.zapier.webhook import unsubscribe
    return unsubscribe(webhook_id=webhook_id, tenant_id=x_tenant_id)


@app.get("/integrations/zapier", dependencies=[Depends(require_api_key)])
async def zapier_list(x_tenant_id: str = Header(...)):
    """List all Zapier webhook subscriptions for this tenant."""
    from tier3.zapier.webhook import list_subscriptions
    subs = list_subscriptions(tenant_id=x_tenant_id)
    return {"subscriptions": subs, "count": len(subs)}


# ── Sprint 6 — Developer API Keys ─────────────────────────────────────────────

@app.post("/api/keys", dependencies=[Depends(require_api_key)])
async def create_api_key(body: ApiKeyCreateRequest, x_tenant_id: str = Header(...)):
    """Generate a new developer API key. Plaintext returned once — store immediately."""
    return _api_keys.generate(tenant_id=x_tenant_id, name=body.name)


@app.get("/api/keys", dependencies=[Depends(require_api_key)])
async def list_api_keys(x_tenant_id: str = Header(...)):
    """List all API keys for this tenant (prefix + metadata only)."""
    keys = _api_keys.list_keys(tenant_id=x_tenant_id)
    return {"keys": keys, "count": len(keys)}


@app.delete("/api/keys/{key_id}", dependencies=[Depends(require_api_key)])
async def revoke_api_key(key_id: str, x_tenant_id: str = Header(...)):
    """Revoke a developer API key."""
    return _api_keys.revoke(key_id=key_id, tenant_id=x_tenant_id)


# ── Sprint 6 — Bulk Enrichment ────────────────────────────────────────────────

@app.post("/enrich/bulk-job/csv", dependencies=[Depends(require_api_key)])
async def bulk_enrich_csv(body: BulkEnrichCsvRequest, x_tenant_id: str = Header(...)):
    """Run a bulk enrichment job from CSV text. Columns: first_name, last_name, domain/email/company."""
    job = await _bulk_enrich.run_csv(
        tenant_id=x_tenant_id,
        csv_text=body.csv_text,
        limit=min(body.limit, 200),
    )
    return {
        "job_id": job.job_id,
        "source": job.source,
        "total": job.total,
        "enriched": job.enriched,
        "failed": job.failed,
        "status": job.status,
        "results": job.results,
        "error": job.error,
    }


@app.post("/enrich/bulk-job/icp", dependencies=[Depends(require_api_key)])
async def bulk_enrich_icp(body: BulkEnrichIcpRequest, x_tenant_id: str = Header(...)):
    """Run a bulk enrichment job for all contacts at a domain."""
    job = await _bulk_enrich.run_icp(
        tenant_id=x_tenant_id,
        domain=body.domain,
        limit=min(body.limit, 100),
    )
    return {
        "job_id": job.job_id,
        "source": job.source,
        "total": job.total,
        "enriched": job.enriched,
        "failed": job.failed,
        "status": job.status,
        "results": job.results,
        "error": job.error,
    }


@app.get("/enrich/bulk-job/{job_id}", dependencies=[Depends(require_api_key)])
async def get_bulk_job(job_id: str, x_tenant_id: str = Header(...)):
    """Retrieve a bulk job record by ID."""
    job = _bulk_enrich.get_job(job_id=job_id, tenant_id=x_tenant_id)
    if not job:
        return {"error": "Job not found", "job_id": job_id}
    return job


@app.get("/enrich/bulk-jobs", dependencies=[Depends(require_api_key)])
async def list_bulk_jobs(x_tenant_id: str = Header(...), limit: int = 20):
    """List recent bulk enrichment jobs for this tenant."""
    jobs = _bulk_enrich.list_jobs(tenant_id=x_tenant_id, limit=min(limit, 50))
    return {"jobs": jobs, "count": len(jobs)}


# ── Sprint 6 — Autopilot Full Runner ─────────────────────────────────────────

@app.post("/autopilot/enable", dependencies=[Depends(require_api_key)])
async def autopilot_enable(body: AutopilotConfigRequest, x_tenant_id: str = Header(...)):
    """Enable Autopilot and save ICP config + schedule for this tenant."""
    return await _autopilot.enable(
        tenant_id=x_tenant_id,
        icp=body.icp,
        schedule_hours=body.schedule_hours,
        route_after_warp=body.route_after_warp,
        route_marketplace_id=body.route_marketplace_id or "",
        route_min_score=body.route_min_score,
    )


@app.post("/autopilot/disable", dependencies=[Depends(require_api_key)])
async def autopilot_disable(x_tenant_id: str = Header(...)):
    """Disable Autopilot for this tenant."""
    return await _autopilot.disable(tenant_id=x_tenant_id)


@app.get("/autopilot/config", dependencies=[Depends(require_api_key)])
async def autopilot_config(x_tenant_id: str = Header(...)):
    """Return current Autopilot config for this tenant."""
    config = _autopilot.get_config(tenant_id=x_tenant_id)
    return config or {"enabled": False, "icp": {}, "schedule_hours": 24}


@app.post("/autopilot/run", dependencies=[Depends(require_api_key)])
async def autopilot_run(x_tenant_id: str = Header(...)):
    """
    Trigger one Autopilot cycle manually (or via Cloud Scheduler cron).
    Runs Warp Mode with dedup, throttle, and unsubscribe-rate guard.
    """
    result = await _autopilot.run(tenant_id=x_tenant_id)
    return {
        "tenant_id": result.tenant_id,
        "job_id": result.job_id,
        "leads_found": result.leads_found,
        "sequences_queued": result.sequences_queued,
        "skipped_deduped": result.skipped_deduped,
        "paused": result.paused,
        "pause_reason": result.pause_reason,
        "error": result.error,
    }


# ── Outreach channel event — fire Zapier on globalStatus change ───────────────
# (Zapier dispatch is wired into the existing /outreach/channel/event handler below
#  via a post-handler hook in the channel_state_machine response)


# ── Sprint C — Drip Sequences ─────────────────────────────────────────────────

@app.post("/outreach/sequence/create", dependencies=[Depends(require_api_key)])
async def create_sequence(body: CreateSequenceRequest, x_tenant_id: str = Header(...)):
    """Create a reusable drip sequence template."""
    from modules.m2_outreach.drip_sequences import create_sequence as _create
    return await _create(
        tenant_id=x_tenant_id,
        name=body.name,
        from_email=body.from_email,
        from_name=body.from_name,
        steps=[s.model_dump() for s in body.steps],
    )


@app.get("/outreach/sequences", dependencies=[Depends(require_api_key)])
async def list_sequences(x_tenant_id: str = Header(...)):
    """List all sequence templates for the tenant."""
    from modules.m2_outreach.drip_sequences import get_sequences
    seqs = await get_sequences(tenant_id=x_tenant_id)
    return {"sequences": seqs, "count": len(seqs)}


@app.post("/outreach/sequence/enroll", dependencies=[Depends(require_api_key)])
async def enroll_in_sequence(body: EnrollContactRequest, x_tenant_id: str = Header(...)):
    """Enroll a contact in a sequence. Step 0 fires on the next tick (≤ 1 hour)."""
    from modules.m2_outreach.drip_sequences import enroll_contact
    return await enroll_contact(
        sequence_id=body.sequence_id,
        tenant_id=x_tenant_id,
        to_email=body.to_email,
        to_name=body.to_name,
        company=body.company,
    )


@app.post("/outreach/sequence/tick", dependencies=[Depends(require_api_key)])
async def sequence_tick(x_tenant_id: str = Header(...)):
    """Manually trigger the sequence step runner (also runs hourly in background)."""
    from modules.m2_outreach.drip_sequences import tick
    return await tick(max_send=100)


# ── Sprint D — Autopilot ICP Runner ──────────────────────────────────────────

@app.post("/outreach/autopilot/run-icp", dependencies=[Depends(require_api_key)])
async def run_icp_autopilot(body: RunIcpAutopilotRequest, x_tenant_id: str = Header(...)):
    """
    One-shot autopilot: search by ICP → enrich contacts → enroll all found emails
    into the specified sequence. Returns stats within the request lifetime.
    """
    from modules.m1_intelligence.company_search import search_companies
    from modules.m1_intelligence.contact_discover import discover_contacts_batch
    from modules.m2_outreach.drip_sequences import enroll_contact

    companies = await search_companies(
        keywords=body.keywords,
        location=body.location,
        industry=body.industry,
        limit=min(body.limit, 50),
    )
    if not companies:
        return {"companies_found": 0, "emails_discovered": 0, "enrolled": 0}

    batch = [
        {
            "index":   i,
            "name":    c.get("name", ""),
            "domain":  c.get("domain", ""),
            "website": c.get("website", ""),
            "phone":   c.get("phone", ""),
        }
        for i, c in enumerate(companies)
    ]
    enriched = await discover_contacts_batch(batch, max_parallel=5)

    enrolled = 0
    for r in enriched:
        if not r.get("email"):
            continue
        c = companies[r["index"]]
        contact_name = f"{r.get('first_name', '')} {r.get('last_name', '')}".strip()
        await enroll_contact(
            sequence_id=body.sequence_id,
            tenant_id=x_tenant_id,
            to_email=r["email"],
            to_name=contact_name,
            company=c.get("name", ""),
        )
        enrolled += 1

    return {
        "companies_found":   len(companies),
        "emails_discovered": enrolled,
        "enrolled":          enrolled,
        "sequence_id":       body.sequence_id,
    }


# ── Webhooks ──────────────────────────────────────────────────────────────────

@app.post("/webhooks/brevo")
async def brevo_webhook(request: Request):
    """
    Receive Brevo delivery/open/click/reply/bounce/unsub events.
    Brevo sends an array of event objects.
    Each event has: event, email, messageId, date, tag (we embed enrollment_id here).
    """
    try:
        payload = await request.json()
    except Exception:
        return {"status": "ok"}

    events = payload if isinstance(payload, list) else [payload]

    from modules.m2_outreach.drip_sequences import update_enrollment_status
    from modules.m2_outreach.channel_state_machine import ChannelStateMachine
    csm = ChannelStateMachine()

    TERMINAL_EVENTS = {
        "hard_bounce": "bounced",
        "unsubscribed": "unsubscribed",
        "spam": "unsubscribed",
    }

    for evt in events:
        event_type = evt.get("event", "")
        tag = evt.get("tag", "")

        # Update channel state machine (keyed by email when no lead_id available)
        email = evt.get("email", "")
        lead_id = tag if tag.startswith("enr_") else email

        if event_type == "opened":
            csm.handle_event(lead_id, "email", "open")
        elif event_type == "click":
            csm.handle_event(lead_id, "email", "open")
        elif event_type == "hard_bounce":
            csm.handle_event(lead_id, "email", "bounce")
        elif event_type == "unsubscribed":
            csm.handle_event(lead_id, "email", "unsubscribe")

        # Pause/stop sequence enrollment on terminal events
        if event_type in TERMINAL_EVENTS and tag:
            await update_enrollment_status(tag, TERMINAL_EVENTS[event_type])

    return {"status": "ok", "processed": len(events)}


@app.post("/webhook/{module}")
async def receive_webhook(module: str, request: Request):
    payload = await request.json()
    return {"status": "received", "module": module, "keys": list(payload.keys()) if isinstance(payload, dict) else []}


# ── Sprint 7 — Route Tab: Marketplace Webhook Router ─────────────────────────

@app.get("/route/marketplaces", dependencies=[Depends(require_api_key)])
async def route_get_marketplaces(x_tenant_id: str = Header(...)):
    """Return all 18 marketplace catalog entries merged with tenant webhook configs."""
    marketplaces = _marketplace.get_marketplace_configs(tenant_id=x_tenant_id)
    return {"marketplaces": marketplaces, "count": len(marketplaces)}


@app.post("/route/marketplace/{marketplace_id}", dependencies=[Depends(require_api_key)])
async def route_save_marketplace(
    marketplace_id: str,
    body: MarketplaceConfigRequest,
    x_tenant_id: str = Header(...),
):
    """Save or update webhook URL, API key, and CPL target for a marketplace."""
    result = _marketplace.save_marketplace_config(
        tenant_id=x_tenant_id,
        marketplace_id=marketplace_id,
        webhook_url=body.webhook_url,
        api_key=body.api_key or "",
        cpl=body.cpl,
    )
    return result


@app.post("/route/test-webhook", dependencies=[Depends(require_api_key)])
async def route_test_webhook(body: WebhookTestRequest, x_tenant_id: str = Header(...)):
    """Send a sample lead payload to a webhook URL and return the HTTP result."""
    result = await _marketplace.test_webhook(
        webhook_url=body.webhook_url,
        api_key=body.api_key or "",
    )
    return result


@app.post("/route/dispatch", dependencies=[Depends(require_api_key)])
async def route_dispatch(body: RouteDispatchRequest, x_tenant_id: str = Header(...)):
    """
    Route selected leads to a buyer marketplace webhook.
    ping_post=True dispatches to all configured marketplaces simultaneously.
    TCPA compliance is the caller's responsibility — consent records must exist.
    """
    result = await _marketplace.dispatch(
        tenant_id=x_tenant_id,
        marketplace_id=body.marketplace_id,
        leads=body.leads,
        ping_post=body.ping_post,
    )
    return {
        "session_id":         result.session_id,
        "marketplace_id":     result.marketplace_id,
        "marketplace_name":   result.marketplace_name,
        "leads_routed":       result.leads_routed,
        "estimated_earnings": result.estimated_earnings,
        "failed":             result.failed,
        "error":              result.error,
    }


@app.get("/route/sessions", dependencies=[Depends(require_api_key)])
async def route_sessions(x_tenant_id: str = Header(...), limit: int = 20):
    """Return recent routing sessions with earnings for this tenant."""
    sessions = _marketplace.get_sessions(tenant_id=x_tenant_id, limit=min(limit, 50))
    total_earned = sum(s.get("estimated_earnings", 0) for s in sessions)
    return {"sessions": sessions, "count": len(sessions), "total_earned": total_earned}


# ── Sprint 8 — Race Agents: CPL Auction (Bass.EXE) ───────────────────────────

@app.post("/race/run", dependencies=[Depends(require_api_key)])
async def race_run(body: RaceDispatchRequest, x_tenant_id: str = Header(...)):
    """
    Run CPL auction across all configured marketplaces.
    Pings all simultaneously, routes each lead to the highest bidder.
    Returns per-lead auction results.
    """
    results = await _race.run_bulk(
        tenant_id=x_tenant_id,
        leads=body.leads,
        timeout=body.timeout,
    )
    serialized = [
        {
            "auction_id":              r.auction_id,
            "lead_id":                 r.lead_id,
            "winner_marketplace_id":   r.winner_marketplace_id,
            "winner_marketplace_name": r.winner_marketplace_name,
            "winning_cpl":             r.winning_cpl,
            "all_bids":                r.all_bids,
            "dispatched":              r.dispatched,
            "error":                   r.error,
            "created_at":              r.created_at,
        }
        for r in results
    ]
    total_earned = sum(r.winning_cpl for r in results if r.dispatched)
    return {
        "results":       serialized,
        "total_auctions": len(results),
        "auctions_won":  sum(1 for r in results if r.dispatched),
        "total_earned":  round(total_earned, 2),
    }


@app.get("/race/results", dependencies=[Depends(require_api_key)])
async def race_results(x_tenant_id: str = Header(...), limit: int = 20):
    """Return recent CPL auction results + aggregate stats for this tenant."""
    return _race.get_results(tenant_id=x_tenant_id, limit=min(limit, 50))


# ── Sprint 9B — Campaign Landing Pages ───────────────────────────────────────

@app.post("/campaign-pages", dependencies=[Depends(require_api_key)])
async def create_campaign_page(body: CampaignPageCreateRequest, x_tenant_id: str = Header(...)):
    """Create a new campaign landing page config. The slug becomes the URL: /c/{slug}"""
    from supabase import create_client
    import uuid as _uuid
    from datetime import datetime, timezone
    db = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"])
    page_id = str(_uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    slug = body.slug.lower().strip().replace(" ", "-")
    row = {
        "id": page_id, "tenant_id": x_tenant_id,
        "slug": slug, "headline": body.headline,
        "subheadline": body.subheadline, "cta_text": body.cta_text,
        "brand_color": body.brand_color, "form_fields": body.form_fields,
        "logo_url": body.logo_url, "company_name": body.company_name,
        "campaign_id": body.campaign_id, "created_at": now,
    }
    db.table("urap_campaign_pages").insert(row).execute()
    return row


@app.get("/campaign-pages", dependencies=[Depends(require_api_key)])
async def list_campaign_pages(x_tenant_id: str = Header(...)):
    """Return all landing pages for this tenant."""
    from supabase import create_client
    db = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"])
    resp = (
        db.table("urap_campaign_pages")
        .select("id, slug, headline, subheadline, cta_text, brand_color, form_fields, company_name, campaign_id, created_at")
        .eq("tenant_id", x_tenant_id)
        .order("created_at", desc=True)
        .execute()
    )
    return {"pages": resp.data or [], "count": len(resp.data or [])}


@app.get("/p/{slug}")
async def get_campaign_page_public(slug: str, x_tenant_id: str = Header(default="dev-tenant")):
    """Public — fetched by the dabblin-landing-pages Next.js app at render time."""
    from supabase import create_client
    db = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"])
    resp = (
        db.table("urap_campaign_pages")
        .select("*")
        .eq("slug", slug)
        .limit(1)
        .execute()
    )
    if not resp.data:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="page_not_found")
    return {"page": resp.data[0]}


@app.delete("/campaign-pages/{page_id}", dependencies=[Depends(require_api_key)])
async def delete_campaign_page(page_id: str, x_tenant_id: str = Header(...)):
    from supabase import create_client
    db = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"])
    db.table("urap_campaign_pages").delete().eq("id", page_id).eq("tenant_id", x_tenant_id).execute()
    return {"deleted": True, "page_id": page_id}


# ── Sprint 9A — Campaign Lists (contact-based) ───────────────────────────────

@app.post("/campaigns/lists", dependencies=[Depends(require_api_key)])
async def create_campaign_list(body: CampaignListSaveRequest, x_tenant_id: str = Header(...)):
    """Save a named contact list from Prospector results."""
    from supabase import create_client
    import uuid as _uuid
    from datetime import datetime, timezone
    db = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"])
    list_id = str(_uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    db.table("urap_campaign_lists").insert({
        "id": list_id, "tenant_id": x_tenant_id,
        "name": body.name.strip(), "contact_count": len(body.contacts), "created_at": now,
    }).execute()
    rows = [
        {
            "id": str(_uuid.uuid4()), "list_id": list_id, "tenant_id": x_tenant_id,
            "lead_id": c.lead_id or str(_uuid.uuid4()),
            "name": c.name, "title": c.title, "company": c.company,
            "email": c.email, "phone": c.phone or "",
            "email_verified": c.email_verified, "enrichment_source": c.enrichment_source,
        }
        for c in body.contacts if c.email
    ]
    for i in range(0, len(rows), 50):
        db.table("urap_campaign_list_contacts").insert(rows[i:i+50]).execute()
    return {"list_id": list_id, "name": body.name.strip(), "count": len(rows), "created_at": now}


@app.get("/campaigns/lists", dependencies=[Depends(require_api_key)])
async def get_campaign_lists(x_tenant_id: str = Header(...)):
    """Return all contact lists for this tenant (campaign lists + company lists merged)."""
    from supabase import create_client
    db = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"])
    camp_resp = (
        db.table("urap_campaign_lists")
        .select("id, name, contact_count, created_at")
        .eq("tenant_id", x_tenant_id)
        .order("created_at", desc=True)
        .execute()
    )
    company_resp = (
        db.table("urap_lead_lists")
        .select("id, name, item_count, created_at")
        .eq("tenant_id", x_tenant_id)
        .order("created_at", desc=True)
        .execute()
    )
    campaign_lists = camp_resp.data or []
    company_lists = [
        {"id": f"company:{r['id']}", "name": r["name"], "contact_count": r.get("item_count", 0), "created_at": r["created_at"]}
        for r in (company_resp.data or [])
    ]
    merged = campaign_lists + company_lists
    merged.sort(key=lambda x: x["created_at"], reverse=True)
    return {"lists": merged, "count": len(merged)}


@app.delete("/campaigns/lists/{list_id}", dependencies=[Depends(require_api_key)])
async def delete_campaign_list(list_id: str, x_tenant_id: str = Header(...)):
    from supabase import create_client
    db = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"])
    db.table("urap_campaign_lists").delete().eq("id", list_id).eq("tenant_id", x_tenant_id).execute()
    return {"deleted": True, "list_id": list_id}


# ── Sprint 9A — Campaigns ─────────────────────────────────────────────────────

@app.post("/campaigns", dependencies=[Depends(require_api_key)])
async def create_campaign(body: CampaignCreateRequest, x_tenant_id: str = Header(...)):
    """Create a new campaign (status: draft)."""
    from supabase import create_client
    import uuid as _uuid
    from datetime import datetime, timezone
    db = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"])
    campaign_id = str(_uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    row = {
        "id": campaign_id, "tenant_id": x_tenant_id,
        "name": body.name.strip(), "list_id": body.list_id,
        "from_email": body.from_email, "from_name": body.from_name,
        "subject_template": body.subject_template, "body_template": body.body_template,
        "ai_personalize": body.ai_personalize,
        "status": "draft", "sent_count": 0, "failed_count": 0, "created_at": now,
    }
    db.table("urap_campaigns").insert(row).execute()
    return row


@app.get("/campaigns", dependencies=[Depends(require_api_key)])
async def list_campaigns(x_tenant_id: str = Header(...)):
    """Return all campaigns for this tenant."""
    from supabase import create_client
    db = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"])
    resp = (
        db.table("urap_campaigns")
        .select("id, name, list_id, from_email, from_name, subject_template, ai_personalize, status, sent_count, failed_count, created_at")
        .eq("tenant_id", x_tenant_id)
        .order("created_at", desc=True)
        .execute()
    )
    return {"campaigns": resp.data or [], "count": len(resp.data or [])}


@app.post("/campaigns/generate-templates", dependencies=[Depends(require_api_key)])
async def generate_templates(body: GenerateTemplatesRequest, x_tenant_id: str = Header(...)):
    """Generate cold email template subject + HTML body using Gemini Flash based on list name context."""
    from supabase import create_client
    import httpx
    import json
    
    db = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"])
    
    list_name = "potential leads"
    raw_list_id = body.list_id
    try:
        if raw_list_id.startswith("company:"):
            actual_id = raw_list_id[len("company:"):]
            resp = db.table("urap_lead_lists").select("name").eq("id", actual_id).eq("tenant_id", x_tenant_id).execute()
            if resp.data:
                list_name = resp.data[0]["name"]
        else:
            resp = db.table("urap_campaign_lists").select("name").eq("id", raw_list_id).eq("tenant_id", x_tenant_id).execute()
            if resp.data:
                list_name = resp.data[0]["name"]
    except Exception as exc:
        print(f"[generate-templates] Error fetching list name: {exc}")

    # Fallback default template
    subject = "Quick question about {{company}}"
    body_html = (
        "<p>Hi {{first_name}},</p>\n"
        "<p>{{personalized_opener}} I noticed you're leading efforts as {{title}} at {{company}}.</p>\n"
        "<p>We work with companies in your space to help streamline B2B growth and run outreach automation.</p>\n"
        "<p>Are you open to a brief 10-minute call sometime this week to see if there is a mutual fit?</p>\n"
        "<p>Best,</p>"
    )

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if api_key:
        GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        prompt = f"""You are an expert B2B sales copywriter. Write a highly personalized cold outreach email template designed for contacts on a list named: "{list_name}".

The template MUST use placeholders that will be replaced dynamically later. Available placeholders are:
- `{{name}}` (Full Name)
- `{{first_name}}` (First Name)
- `{{company}}` (Company Name)
- `{{title}}` (Job Title)
- `{{personalized_opener}}` (Personalized AI opening sentence generated for the lead)

Rules for copy:
- Subject: 6–8 words, no emojis, curiosity-driven, no "quick" or "just" (can use placeholders, e.g. "Question about {{company}}")
- Body: 2 to 3 short paragraphs, under 150 words total
- Tone: direct, peer-to-peer, professional, no hype
- First paragraph MUST start with, or naturally integrate, `{{personalized_opener}}`
- Single clear CTA: propose a 15-minute call this week

Return valid JSON only: {{"subject": "...", "body_html": "<p>...</p><p>...</p><p>...</p>"}}"""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{GEMINI_URL}?key={api_key}",
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"responseMimeType": "application/json"},
                    },
                    timeout=30,
                )
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(text)
                subject = parsed.get("subject", subject)
                body_html = parsed.get("body_html", body_html)
        except Exception as e:
            print(f"[generate-templates] Gemini error: {e}")

    return {"subject": subject, "body_html": body_html}


@app.post("/campaigns/{campaign_id}/dispatch", dependencies=[Depends(require_api_key)])
async def dispatch_campaign(campaign_id: str, x_tenant_id: str = Header(...)):
    """Personalize + batch-send a campaign to its list. Returns a StreamingResponse with send progress."""
    from supabase import create_client
    from modules.m2_outreach.campaign_dispatcher import dispatch_stream
    db = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"])

    # fetch campaign
    camp_resp = db.table("urap_campaigns").select("*").eq("id", campaign_id).eq("tenant_id", x_tenant_id).execute()
    if not camp_resp.data:
        async def err_generator():
            import json
            yield json.dumps({"event": "error", "error": "campaign_not_found"}) + "\n"
        return StreamingResponse(err_generator(), media_type="application/x-ndjson")
    campaign = camp_resp.data[0]

    # mark as sending
    db.table("urap_campaigns").update({"status": "sending"}).eq("id", campaign_id).execute()

    # fetch contacts — support both campaign lists and company lists
    raw_list_id: str = campaign["list_id"]
    if raw_list_id.startswith("company:"):
        actual_id = raw_list_id[len("company:"):]
        items_resp = (
            db.table("urap_lead_list_items")
            .select("company_name, contact_name, contact_title, email, phone")
            .eq("list_id", actual_id)
            .execute()
        )
        contacts = [
            {
                "name": r.get("contact_name") or r.get("company_name", ""),
                "first_name": (r.get("contact_name") or "").split()[0] if r.get("contact_name") else r.get("company_name", ""),
                "company": r.get("company_name", ""),
                "title": r.get("contact_title", ""),
                "email": r.get("email", ""),
                "phone": r.get("phone", ""),
            }
            for r in (items_resp.data or [])
        ]
    else:
        contacts_resp = (
            db.table("urap_campaign_list_contacts")
            .select("lead_id, name, title, company, email, phone, email_verified, enrichment_source")
            .eq("list_id", raw_list_id)
            .eq("tenant_id", x_tenant_id)
            .execute()
        )
        contacts = contacts_resp.data or []

    return StreamingResponse(
        dispatch_stream(
            campaign=campaign,
            contacts=contacts,
            tenant_id=x_tenant_id,
            email_svc=_email_svc,
            db=db,
        ),
        media_type="application/x-ndjson"
    )


@app.get("/campaigns/{campaign_id}/stats", dependencies=[Depends(require_api_key)])
async def campaign_stats(campaign_id: str, x_tenant_id: str = Header(...)):
    """Return send stats for a campaign."""
    from supabase import create_client
    db = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"])
    camp_resp = db.table("urap_campaigns").select("id, name, status, sent_count, failed_count").eq("id", campaign_id).eq("tenant_id", x_tenant_id).execute()
    if not camp_resp.data:
        return {"error": "campaign_not_found"}
    camp = camp_resp.data[0]
    sends_resp = db.table("urap_campaign_sends").select("status, provider, error").eq("campaign_id", campaign_id).execute()
    sends = sends_resp.data or []
    return {**camp, "total_sends": len(sends), "sends": sends[:50]}


# ── Background: hourly sequence tick ─────────────────────────────────────────

async def _sequence_tick_loop():
    await asyncio.sleep(60)  # wait for startup to finish before first run
    while True:
        try:
            from modules.m2_outreach.drip_sequences import tick
            await tick(max_send=100)
        except Exception:
            pass
        await asyncio.sleep(3600)  # every hour


@app.on_event("startup")
async def startup():
    asyncio.create_task(_sequence_tick_loop())


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
