# Graph Report - urap  (2026-09-14)

## Corpus Check
- 99 files · ~212,931 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1062 nodes · 4601 edges · 46 communities detected
- Extraction: 25% EXTRACTED · 75% INFERRED · 0% AMBIGUOUS · INFERRED: 3472 edges (avg confidence: 0.51)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 63|Community 63]]
- [[_COMMUNITY_Community 64|Community 64]]
- [[_COMMUNITY_Community 65|Community 65]]
- [[_COMMUNITY_Community 66|Community 66]]
- [[_COMMUNITY_Community 67|Community 67]]
- [[_COMMUNITY_Community 68|Community 68]]
- [[_COMMUNITY_Community 69|Community 69]]
- [[_COMMUNITY_Community 70|Community 70]]
- [[_COMMUNITY_Community 71|Community 71]]
- [[_COMMUNITY_Community 72|Community 72]]
- [[_COMMUNITY_Community 73|Community 73]]
- [[_COMMUNITY_Community 74|Community 74]]
- [[_COMMUNITY_Community 75|Community 75]]
- [[_COMMUNITY_Community 76|Community 76]]
- [[_COMMUNITY_Community 77|Community 77]]

## God Nodes (most connected - your core abstractions)
1. `EnrichmentService` - 295 edges
2. `WarpModeAgent` - 293 edges
3. `EmailSequenceService` - 290 edges
4. `ChannelStateMachine` - 267 edges
5. `AutopilotRunner` - 258 edges
6. `MarketplaceRouter` - 253 edges
7. `ConsentLedgerService` - 252 edges
8. `BulkEnrichRunner` - 246 edges
9. `ReplyIntelligenceAgent` - 246 edges
10. `LeadRouterService` - 245 edges

## Surprising Connections (you probably didn't know these)
- `URAP Platform` --references--> `URAP Full Logo (Dark Background)`  [INFERRED]
  README.md → urap-app/URAP Logo.png
- `test_sector_survives_warp_generation()` --calls--> `WarpModeAgent`  [INFERRED]
  urap-engine/tests/test_click_followups.py → urap-engine/modules/m3_agents/warp_mode.py
- `test_outreach_html_has_one_explicit_demo_link()` --calls--> `build_outreach_html()`  [INFERRED]
  urap-engine/tests/test_autopilot_multisector.py → urap-engine/modules/m5_api/autopilot_runner.py
- `test_multisector_run_sources_and_keeps_every_sector()` --calls--> `AutopilotRunner`  [INFERRED]
  urap-engine/tests/test_autopilot_multisector.py → urap-engine/modules/m5_api/autopilot_runner.py
- `test_warp_mode_accepts_batches_larger_than_25()` --calls--> `WarpModeAgent`  [INFERRED]
  urap-engine/tests/test_autopilot_multisector.py → urap-engine/modules/m3_agents/warp_mode.py

## Hyperedges (group relationships)
- **URAP Three-Component Plugin System** — urap_app_component, urap_engine_component, urap_core_component [EXTRACTED 1.00]
- **URAP Six Functional Modules** — m1_intelligence, m2_outreach, m3_agents, m4_inbound, m5_api, m6_compliance [EXTRACTED 1.00]
- **Email Sending Provider Waterfall** — email_sender_waterfall, tier3_integrations [EXTRACTED 1.00]
- **AI Agent Pipeline: Warp Mode + Reply Intelligence** — warp_mode, reply_intelligence, google_adk, google_calendar_tier3, telegram_tier3 [EXTRACTED 1.00]
- **TCPA Compliance Chain** — consent_ledger, trustedform, urap_core_component, m6_compliance [EXTRACTED 1.00]

## Communities

### Community 0 - "Community 0"
Cohesion: 0.02
Nodes (140): BaseModel, Enum, create_discovery_call(), _get_service(), Tier 3 — Google Calendar: create discovery call events on meeting_set triggers., Create a 30-min discovery call event. Returns HTML link or '' on failure.      s, discover_contacts_batch(), Enrich a batch. Each dict needs: index, name, domain, website, phone. (+132 more)

### Community 1 - "Community 1"
Cohesion: 0.1
Nodes (131): ChannelStateMachine, ReplyIntelligenceAgent, LeadRouterService, Handles inbound lead capture, ping-post distribution, and Twilio geo-routing., ApiKeyManager, AutopilotRunner, BulkEnrichRunner, ConsentLedgerService (+123 more)

### Community 2 - "Community 2"
Cohesion: 0.03
Nodes (32): fetchConfig(), fetchFollowups(), fetchMarketplaces(), fetchSends(), handleRunNow(), handleToggle(), headers(), syncClicks() (+24 more)

### Community 3 - "Community 3"
Cohesion: 0.05
Nodes (49): CleanlistClient, CleanlistResult, Cleanlist.ai email verification client — quality gate (all waterfall results pas, HunterClient, HunterResult, Hunter.io email enrichment client — domain sweep layer (waterfall layer 3 / bulk, Pull all publicly known emails at a domain., _build_contact() (+41 more)

### Community 4 - "Community 4"
Cohesion: 0.07
Nodes (73): EmailSequenceService, WarpModeAgent, MarketplaceRouter, Routes enriched URAP contacts to external buyer marketplace webhooks., Disable autopilot for a tenant., Return autopilot config for a tenant.          Falls back to the AUTOPILOT_CONFI, Execute one Autopilot cycle for a tenant.         Called by Cloud Scheduler (or, Execute one Autopilot cycle for a tenant.         Called by Cloud Scheduler (or (+65 more)

### Community 5 - "Community 5"
Cohesion: 0.05
Nodes (29): sms_send(), voice_dial(), voice_hangup(), voice_status(), client(), URAP Engine — E2E golden path test suite.  Tests the full request lifecycle agai, Email send should fail gracefully (not 500) when SMTP keys absent., Warp Mode should complete (with fallback copy) even without AI keys. (+21 more)

### Community 6 - "Community 6"
Cohesion: 0.07
Nodes (17): BrevoClient, Brevo (formerly Sendinblue) email sender — overflow provider.  Free tier: ~9,000, SendResult, EmailSequence, Module II — Email sequence orchestrator.  Send waterfall: SMTP2GO (primary) → Br, Simple intent score from enrichment signals (0–100).         Full intent scoring, Simple intent score from enrichment signals (0–100).         Full intent scoring, Send one email through the provider waterfall.         TCPA gate only blocks if (+9 more)

### Community 7 - "Community 7"
Cohesion: 0.07
Nodes (46): ReversePhoneService, RaceAuction, CPL auction engine. Pings all configured marketplaces simultaneously,     picks, ApiKeyCreateRequest, CompanyContactBatchItem, IntentScoreRequest, PeopleSearchRequest, Create a reusable drip sequence template. (+38 more)

### Community 8 - "Community 8"
Cohesion: 0.07
Nodes (22): Module III — Warp Mode AI Copilot.  Given an ICP, autonomously:   1. Queries the, Refine draft via Claude Sonnet. Returns (subject, body_html, was_reviewed)., Static template fallback when AI APIs are not configured., Run a full Warp Mode job: enrich → generate copy → store → alert.          icp k, Return recent Warp Mode jobs for this tenant, newest first., Generate draft subject + body via Gemini Flash. Returns ("", "") on failure., WarpJobResult, WarpLead (+14 more)

### Community 9 - "Community 9"
Cohesion: 0.08
Nodes (31): _apollo_search(), _dedup_results(), _foursquare_search(), _google_places_search(), _hunter_domain(), _places_industry(), Company search — two modes:   1. Domain enrichment: domain provided → Hunter.io, Merge results from multiple sources, dedup by phone or name+location. (+23 more)

### Community 10 - "Community 10"
Cohesion: 0.07
Nodes (30): EnrichmentService, Refine draft via Claude Sonnet. Returns (subject, body_html, was_reviewed)., Refine draft via Claude Sonnet. Returns (subject, body_html, was_reviewed)., Refine draft via Claude Sonnet. Returns (subject, body_html, was_reviewed)., Static template fallback when AI APIs are not configured., Static template fallback when AI APIs are not configured., Static template fallback when AI APIs are not configured., Run a full Warp Mode job: enrich → generate copy → store → alert.          icp k (+22 more)

### Community 11 - "Community 11"
Cohesion: 0.1
Nodes (18): ClaimResult, _db(), InboundLead, _infer_company_size(), _infer_title_level(), PreviewAttributes, Module IV — Inbound Lead Capture & Distribution (Sprint 5)., Step 1 of ping-post: receive inbound lead, enrich, store in Supabase.         Re (+10 more)

### Community 12 - "Community 12"
Cohesion: 0.13
Nodes (10): BidResult, _db(), RaceResult, Race Agents — CPL auction: simultaneous ping to all configured marketplaces, hig, Run CPL auction for each lead sequentially (avoids hammering marketplaces)., Return recent auction results + aggregate stats., Send auction ping to one marketplace. Returns CPL from response or config fallba, Pull all configured marketplace webhooks for this tenant + merge catalog names. (+2 more)

### Community 13 - "Community 13"
Cohesion: 0.12
Nodes (8): _digits(), Module I — Reverse phone lookup.  Unlike the email enrichment waterfall, every l, Search our own tables for the number.          Phone formatting is inconsistent, Search the AI receptionist's call log — the record of who actually         calle, Pick the best available name, most-trusted source first., Condense a postgrest APIError to something an operator can act on., _skipped(), _supabase_reason()

### Community 14 - "Community 14"
Cohesion: 0.13
Nodes (9): _db(), DispatchResult, Module IV — Marketplace Webhook Router (Phase 1 Route Core, BizReach integration, Upsert marketplace webhook config for a tenant., Dispatch a set of leads to a single target with a 3-attempt retry loop., Route selected leads to configured marketplace webhooks.         If ping_post=Tr, Return recent routing sessions for a tenant., Map URAP contact fields to the standardized marketplace payload schema. (+1 more)

### Community 15 - "Community 15"
Cohesion: 0.22
Nodes (5): _default_channel_state(), Module II — Omni-Channel Outreach: channel state machine.  Core rule: a reply on, Check if a channel is in a sendable state before queuing outreach., Advance to candidate only if it outranks current. Never downgrade., Call when a reply arrives on any channel.         Pauses all other channels, upg

### Community 16 - "Community 16"
Cohesion: 0.15
Nodes (7): BulkJob, _db(), Bulk enrichment runner — CSV list or ICP-filter batch jobs., Retrieve a bulk job record from Supabase., List recent bulk jobs for a tenant (summary only — no per-row results)., Enrich contacts from CSV text.         Expected columns (order-insensitive): fir, Bulk-enrich all contacts at a domain via the enrichment waterfall.         Wraps

### Community 17 - "Community 17"
Cohesion: 0.17
Nodes (14): _db(), delete_list(), get_list_items(), get_lists(), Lead list management — saves search results + enriched contacts to Supabase.  Ta, Create a named lead list and insert all items.     Each item dict may contain: n, Return all lists for a tenant, most recent first., Return all items in a specific list. (+6 more)

### Community 18 - "Community 18"
Cohesion: 0.23
Nodes (13): discover_contact(), _guess_domain_from_name(), _hunter_find(), _is_listing(), Contact discovery — two strategies in priority order:   1. Hunter.io domain sear, Discover contact info for a single business.     Returns: { email, first_name, l, Scrape the homepage for social media profile links., Fetch the real business website URL from Yelp's details endpoint. (+5 more)

### Community 19 - "Community 19"
Cohesion: 0.19
Nodes (11): dispatch(), dispatch_stream(), _haiku_opener(), Module II — Campaign dispatcher with AI personalization.  Batch-sends a campaign, Dispatch campaign to all contacts and yield progress events as NDJSON., Dispatch campaign to all contacts. Returns {sent, failed, skipped}., _render(), dispatch_campaign() (+3 more)

### Community 20 - "Community 20"
Cohesion: 0.33
Nodes (6): fetchAll(), fetchContacts(), fetchMarketplaces(), fetchSessions(), handleRoute(), headers()

### Community 21 - "Community 21"
Cohesion: 0.25
Nodes (2): _FakeAsyncClient, _FakeResponse

### Community 22 - "Community 22"
Cohesion: 0.22
Nodes (9): Antigravity / Dabblin Cloud Technologies, Multi-Tenant Design, URAP — Unified Revenue Acceleration Platform, URAP Sprint Roadmap (Sprints 0-9), Supabase Data Tables, URAP Full Logo (Dark Background), URAP Icon Logo, urap-logo.png (in-app asset) (+1 more)

### Community 23 - "Community 23"
Cohesion: 0.29
Nodes (3): Insert a consent record. Raises on DB error — caller must handle., Return True if at least one consent record exists for this lead., Return the most recent consent record for a lead, or None.

### Community 24 - "Community 24"
Cohesion: 0.4
Nodes (3): Numverify phone validation client — free-tier carrier/line-type fallback.  Used, Return {ok, data, error}. Never raises — this is one waterfall layer., validate_number()

### Community 25 - "Community 25"
Cohesion: 0.5
Nodes (1): URAP Engine — request auth middleware.  API key validation via X-Api-Key header.

### Community 27 - "Community 27"
Cohesion: 1.0
Nodes (1): Module VI — Security, Compliance & Trust: TCPA consent ledger.  Consent records

### Community 29 - "Community 29"
Cohesion: 1.0
Nodes (2): Contact Enrichment Waterfall, Hunter.io Email Enrichment

### Community 60 - "Community 60"
Cohesion: 1.0
Nodes (1): Return all contact lists for this tenant (campaign lists + company lists merged)

### Community 61 - "Community 61"
Cohesion: 1.0
Nodes (1): Return all contact lists for this tenant (campaign lists + company lists merged)

### Community 62 - "Community 62"
Cohesion: 1.0
Nodes (1): Pull contacts at a domain via search-person + enrich in one pass.

### Community 63 - "Community 63"
Cohesion: 1.0
Nodes (1): urap-app — React + Vite Frontend Dashboard

### Community 64 - "Community 64"
Cohesion: 1.0
Nodes (1): urap-engine — Python FastAPI Microservice

### Community 65 - "Community 65"
Cohesion: 1.0
Nodes (1): @antigravity/urap-core — Express Middleware Plugin

### Community 66 - "Community 66"
Cohesion: 1.0
Nodes (1): LeadStatusObject

### Community 67 - "Community 67"
Cohesion: 1.0
Nodes (1): Email Sender Waterfall (SMTP2GO → Brevo → Mailgun)

### Community 68 - "Community 68"
Cohesion: 1.0
Nodes (1): FastAPI 0.115

### Community 69 - "Community 69"
Cohesion: 1.0
Nodes (1): Supabase Python Client

### Community 70 - "Community 70"
Cohesion: 1.0
Nodes (1): Stripe Metered Billing

### Community 71 - "Community 71"
Cohesion: 1.0
Nodes (1): Twilio Voice/SMS Integration

### Community 72 - "Community 72"
Cohesion: 1.0
Nodes (1): Google ADK + OpenRouter (AI Agent Pattern)

### Community 73 - "Community 73"
Cohesion: 1.0
Nodes (1): Google Cloud Run Deployment Target

### Community 74 - "Community 74"
Cohesion: 1.0
Nodes (1): TrustedForm TCPA Consent Integration

### Community 75 - "Community 75"
Cohesion: 1.0
Nodes (1): React 19 + Vite 6

### Community 76 - "Community 76"
Cohesion: 1.0
Nodes (1): Tailwind CSS 3

### Community 77 - "Community 77"
Cohesion: 1.0
Nodes (1): React Router v7

## Knowledge Gaps
- **140 isolated node(s):** `URAP Engine — E2E golden path test suite.  Tests the full request lifecycle agai`, `Synchronous httpx client for the full test session.`, `Email send should fail gracefully (not 500) when SMTP keys absent.`, `Warp Mode should complete (with fallback copy) even without AI keys.`, `SMS should be blocked by TCPA gate for unconsented lead.` (+135 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 21`** (9 nodes): `_FakeAsyncClient`, `.__aenter__()`, `.__aexit__()`, `.__init__()`, `.post()`, `_FakeResponse`, `.json()`, `test_domain_search_uses_current_prospeo_schema()`, `test_prospeo_client.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 25`** (4 nodes): `get_api_key()`, `URAP Engine — request auth middleware.  API key validation via X-Api-Key header.`, `require_api_key()`, `middleware.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 27`** (2 nodes): `Module VI — Security, Compliance & Trust: TCPA consent ledger.  Consent records`, `consent_ledger.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 29`** (2 nodes): `Contact Enrichment Waterfall`, `Hunter.io Email Enrichment`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 60`** (1 nodes): `Return all contact lists for this tenant (campaign lists + company lists merged)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 61`** (1 nodes): `Return all contact lists for this tenant (campaign lists + company lists merged)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 62`** (1 nodes): `Pull contacts at a domain via search-person + enrich in one pass.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 63`** (1 nodes): `urap-app — React + Vite Frontend Dashboard`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 64`** (1 nodes): `urap-engine — Python FastAPI Microservice`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 65`** (1 nodes): `@antigravity/urap-core — Express Middleware Plugin`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 66`** (1 nodes): `LeadStatusObject`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 67`** (1 nodes): `Email Sender Waterfall (SMTP2GO → Brevo → Mailgun)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 68`** (1 nodes): `FastAPI 0.115`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 69`** (1 nodes): `Supabase Python Client`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 70`** (1 nodes): `Stripe Metered Billing`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 71`** (1 nodes): `Twilio Voice/SMS Integration`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 72`** (1 nodes): `Google ADK + OpenRouter (AI Agent Pattern)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 73`** (1 nodes): `Google Cloud Run Deployment Target`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 74`** (1 nodes): `TrustedForm TCPA Consent Integration`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 75`** (1 nodes): `React 19 + Vite 6`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 76`** (1 nodes): `Tailwind CSS 3`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 77`** (1 nodes): `React Router v7`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `EnrichmentService` connect `Community 10` to `Community 0`, `Community 1`, `Community 3`, `Community 4`, `Community 7`, `Community 8`, `Community 11`, `Community 16`?**
  _High betweenness centrality (0.183) - this node is a cross-community bridge._
- **Why does `WarpModeAgent` connect `Community 4` to `Community 0`, `Community 1`, `Community 6`, `Community 7`, `Community 8`, `Community 10`, `Community 19`?**
  _High betweenness centrality (0.066) - this node is a cross-community bridge._
- **Why does `ClickFollowups` connect `Community 0` to `Community 1`, `Community 4`, `Community 6`, `Community 7`, `Community 10`?**
  _High betweenness centrality (0.059) - this node is a cross-community bridge._
- **Are the 287 inferred relationships involving `EnrichmentService` (e.g. with `EnrichRequest` and `BulkEnrichRequest`) actually correct?**
  _`EnrichmentService` has 287 INFERRED edges - model-reasoned connections that need verification._
- **Are the 284 inferred relationships involving `WarpModeAgent` (e.g. with `Query` and `DB`) actually correct?**
  _`WarpModeAgent` has 284 INFERRED edges - model-reasoned connections that need verification._
- **Are the 286 inferred relationships involving `EmailSequenceService` (e.g. with `EnrichRequest` and `BulkEnrichRequest`) actually correct?**
  _`EmailSequenceService` has 286 INFERRED edges - model-reasoned connections that need verification._
- **Are the 254 inferred relationships involving `ChannelStateMachine` (e.g. with `EnrichRequest` and `BulkEnrichRequest`) actually correct?**
  _`ChannelStateMachine` has 254 INFERRED edges - model-reasoned connections that need verification._