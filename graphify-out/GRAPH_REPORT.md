# Graph Report - urap  (2026-08-20)

## Corpus Check
- 96 files · ~209,630 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 948 nodes · 3749 edges · 41 communities detected
- Extraction: 28% EXTRACTED · 72% INFERRED · 0% AMBIGUOUS · INFERRED: 2708 edges (avg confidence: 0.51)
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
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
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

## God Nodes (most connected - your core abstractions)
1. `EnrichmentService` - 249 edges
2. `WarpModeAgent` - 238 edges
3. `EmailSequenceService` - 238 edges
4. `ChannelStateMachine` - 225 edges
5. `AutopilotRunner` - 212 edges
6. `ConsentLedgerService` - 210 edges
7. `BulkEnrichRunner` - 205 edges
8. `ReplyIntelligenceAgent` - 204 edges
9. `LeadRouterService` - 204 edges
10. `ApiKeyManager` - 201 edges

## Surprising Connections (you probably didn't know these)
- `URAP Platform` --references--> `URAP Full Logo (Dark Background)`  [INFERRED]
  README.md → urap-app/URAP Logo.png
- `test_multisector_run_sources_and_keeps_every_sector()` --calls--> `AutopilotRunner`  [INFERRED]
  urap-engine/tests/test_autopilot_multisector.py → urap-engine/modules/m5_api/autopilot_runner.py
- `test_warp_mode_accepts_batches_larger_than_25()` --calls--> `WarpModeAgent`  [INFERRED]
  urap-engine/tests/test_autopilot_multisector.py → urap-engine/modules/m3_agents/warp_mode.py
- `Bulk enrichment runner — CSV list or ICP-filter batch jobs.` --uses--> `EnrichmentService`  [INFERRED]
  urap-engine/modules/m5_api/bulk_enrich_runner.py → urap-engine/modules/m1_intelligence/enrichment.py
- `Enrich contacts from CSV text.         Expected columns (order-insensitive): fir` --uses--> `EnrichmentService`  [INFERRED]
  urap-engine/modules/m5_api/bulk_enrich_runner.py → urap-engine/modules/m1_intelligence/enrichment.py

## Hyperedges (group relationships)
- **URAP Three-Component Plugin System** — urap_app_component, urap_engine_component, urap_core_component [EXTRACTED 1.00]
- **URAP Six Functional Modules** — m1_intelligence, m2_outreach, m3_agents, m4_inbound, m5_api, m6_compliance [EXTRACTED 1.00]
- **Email Sending Provider Waterfall** — email_sender_waterfall, tier3_integrations [EXTRACTED 1.00]
- **AI Agent Pipeline: Warp Mode + Reply Intelligence** — warp_mode, reply_intelligence, google_adk, google_calendar_tier3, telegram_tier3 [EXTRACTED 1.00]
- **TCPA Compliance Chain** — consent_ledger, trustedform, urap_core_component, m6_compliance [EXTRACTED 1.00]

## Communities

### Community 0 - "Community 0"
Cohesion: 0.02
Nodes (154): Enum, _apollo_search(), _dedup_results(), _foursquare_search(), _google_places_search(), _hunter_domain(), _places_industry(), Company search — two modes:   1. Domain enrichment: domain provided → Hunter.io (+146 more)

### Community 1 - "Community 1"
Cohesion: 0.1
Nodes (134): EnrichmentService, ChannelStateMachine, ReplyIntelligenceAgent, Refine draft via Claude Sonnet. Returns (subject, body_html, was_reviewed)., Refine draft via Claude Sonnet. Returns (subject, body_html, was_reviewed)., Static template fallback when AI APIs are not configured., Static template fallback when AI APIs are not configured., Run a full Warp Mode job: enrich → generate copy → store → alert.          icp k (+126 more)

### Community 2 - "Community 2"
Cohesion: 0.03
Nodes (30): fetchConfig(), fetchMarketplaces(), fetchSends(), handleRunNow(), handleToggle(), headers(), fetchJobs(), handleRun() (+22 more)

### Community 3 - "Community 3"
Cohesion: 0.05
Nodes (49): CleanlistClient, CleanlistResult, Cleanlist.ai email verification client — quality gate (all waterfall results pas, HunterClient, HunterResult, Hunter.io email enrichment client — domain sweep layer (waterfall layer 3 / bulk, Pull all publicly known emails at a domain., _build_contact() (+41 more)

### Community 4 - "Community 4"
Cohesion: 0.08
Nodes (60): EmailSequenceService, WarpModeAgent, MarketplaceRouter, Routes enriched URAP contacts to external buyer marketplace webhooks., Execute one Autopilot cycle for a tenant.         Called by Cloud Scheduler (or, Compute unsubscribe rate = unsubscribed / total leads in last 7 days., Count sequences queued today for throttle check., Keyword ICP → Apollo company discovery → contact discovery → lead dicts. (+52 more)

### Community 5 - "Community 5"
Cohesion: 0.05
Nodes (31): create_discovery_call(), _get_service(), Tier 3 — Google Calendar: create discovery call events on meeting_set triggers., Create a 30-min discovery call event. Returns HTML link or '' on failure.      s, ParseResult, Module III — Reply Intelligence Agent.  Parses incoming reply text, classifies s, Heuristic fallback when Claude is not configured., Parse a reply, update channel state, fire alerts. Main agent method. (+23 more)

### Community 6 - "Community 6"
Cohesion: 0.12
Nodes (44): BaseModel, ReversePhoneService, RaceAuction, CPL auction engine. Pings all configured marketplaces simultaneously,     picks, ApiKeyCreateRequest, AutopilotConfigRequest, BulkEnrichCsvRequest, BulkEnrichIcpRequest (+36 more)

### Community 7 - "Community 7"
Cohesion: 0.11
Nodes (15): BrevoClient, Brevo (formerly Sendinblue) email sender — overflow provider.  Free tier: ~9,000, SendResult, EmailSequence, Module II — Email sequence orchestrator.  Send waterfall: SMTP2GO (primary) → Br, Simple intent score from enrichment signals (0–100).         Full intent scoring, Send one email through the provider waterfall.         TCPA gate only blocks if, SendResult (+7 more)

### Community 8 - "Community 8"
Cohesion: 0.09
Nodes (17): AutopilotRunResult, build_outreach_html(), _db(), Autopilot runner — cron-triggered Warp Mode scheduler (Sprint 6 full implementat, Disable autopilot for a tenant., Return autopilot config for a tenant.          Falls back to the AUTOPILOT_CONFI, Execute one Autopilot cycle for a tenant.         Called by Cloud Scheduler (or, Add one explicit tracked CTA and the sender signature. (+9 more)

### Community 9 - "Community 9"
Cohesion: 0.08
Nodes (7): URAP Engine — E2E golden path test suite.  Tests the full request lifecycle agai, Email send should fail gracefully (not 500) when SMTP keys absent., Warp Mode should complete (with fallback copy) even without AI keys., SMS should be blocked by TCPA gate for unconsented lead., test_email_send_graceful_without_smtp_key(), test_sms_send_blocked_without_consent(), test_warp_mode_run()

### Community 10 - "Community 10"
Cohesion: 0.1
Nodes (18): ClaimResult, _db(), InboundLead, _infer_company_size(), _infer_title_level(), PreviewAttributes, Module IV — Inbound Lead Capture & Distribution (Sprint 5)., Step 1 of ping-post: receive inbound lead, enrich, store in Supabase.         Re (+10 more)

### Community 11 - "Community 11"
Cohesion: 0.13
Nodes (10): BidResult, _db(), RaceResult, Race Agents — CPL auction: simultaneous ping to all configured marketplaces, hig, Run CPL auction for each lead sequentially (avoids hammering marketplaces)., Return recent auction results + aggregate stats., Send auction ping to one marketplace. Returns CPL from response or config fallba, Pull all configured marketplace webhooks for this tenant + merge catalog names. (+2 more)

### Community 12 - "Community 12"
Cohesion: 0.12
Nodes (8): _digits(), Module I — Reverse phone lookup.  Unlike the email enrichment waterfall, every l, Search our own tables for the number.          Phone formatting is inconsistent, Search the AI receptionist's call log — the record of who actually         calle, Pick the best available name, most-trusted source first., Condense a postgrest APIError to something an operator can act on., _skipped(), _supabase_reason()

### Community 13 - "Community 13"
Cohesion: 0.13
Nodes (9): _db(), DispatchResult, Module IV — Marketplace Webhook Router (Phase 1 Route Core, BizReach integration, Upsert marketplace webhook config for a tenant., Dispatch a set of leads to a single target with a 3-attempt retry loop., Route selected leads to configured marketplace webhooks.         If ping_post=Tr, Return recent routing sessions for a tenant., Map URAP contact fields to the standardized marketplace payload schema. (+1 more)

### Community 14 - "Community 14"
Cohesion: 0.22
Nodes (5): _default_channel_state(), Module II — Omni-Channel Outreach: channel state machine.  Core rule: a reply on, Check if a channel is in a sendable state before queuing outreach., Advance to candidate only if it outranks current. Never downgrade., Call when a reply arrives on any channel.         Pauses all other channels, upg

### Community 15 - "Community 15"
Cohesion: 0.15
Nodes (7): BulkJob, _db(), Bulk enrichment runner — CSV list or ICP-filter batch jobs., Retrieve a bulk job record from Supabase., List recent bulk jobs for a tenant (summary only — no per-row results)., Enrich contacts from CSV text.         Expected columns (order-insensitive): fir, Bulk-enrich all contacts at a domain via the enrichment waterfall.         Wraps

### Community 16 - "Community 16"
Cohesion: 0.23
Nodes (13): discover_contact(), _guess_domain_from_name(), _hunter_find(), _is_listing(), Contact discovery — two strategies in priority order:   1. Hunter.io domain sear, Discover contact info for a single business.     Returns: { email, first_name, l, Scrape the homepage for social media profile links., Fetch the real business website URL from Yelp's details endpoint. (+5 more)

### Community 17 - "Community 17"
Cohesion: 0.33
Nodes (6): fetchAll(), fetchContacts(), fetchMarketplaces(), fetchSessions(), handleRoute(), headers()

### Community 18 - "Community 18"
Cohesion: 0.25
Nodes (2): _FakeAsyncClient, _FakeResponse

### Community 19 - "Community 19"
Cohesion: 0.22
Nodes (9): Antigravity / Dabblin Cloud Technologies, Multi-Tenant Design, URAP — Unified Revenue Acceleration Platform, URAP Sprint Roadmap (Sprints 0-9), Supabase Data Tables, URAP Full Logo (Dark Background), URAP Icon Logo, urap-logo.png (in-app asset) (+1 more)

### Community 20 - "Community 20"
Cohesion: 0.29
Nodes (3): Insert a consent record. Raises on DB error — caller must handle., Return True if at least one consent record exists for this lead., Return the most recent consent record for a lead, or None.

### Community 21 - "Community 21"
Cohesion: 0.5
Nodes (1): URAP Engine — request auth middleware.  API key validation via X-Api-Key header.

### Community 23 - "Community 23"
Cohesion: 1.0
Nodes (1): Module VI — Security, Compliance & Trust: TCPA consent ledger.  Consent records

### Community 25 - "Community 25"
Cohesion: 1.0
Nodes (2): Contact Enrichment Waterfall, Hunter.io Email Enrichment

### Community 56 - "Community 56"
Cohesion: 1.0
Nodes (1): Return all contact lists for this tenant (campaign lists + company lists merged)

### Community 57 - "Community 57"
Cohesion: 1.0
Nodes (1): Pull contacts at a domain via search-person + enrich in one pass.

### Community 58 - "Community 58"
Cohesion: 1.0
Nodes (1): urap-app — React + Vite Frontend Dashboard

### Community 59 - "Community 59"
Cohesion: 1.0
Nodes (1): urap-engine — Python FastAPI Microservice

### Community 60 - "Community 60"
Cohesion: 1.0
Nodes (1): @antigravity/urap-core — Express Middleware Plugin

### Community 61 - "Community 61"
Cohesion: 1.0
Nodes (1): LeadStatusObject

### Community 62 - "Community 62"
Cohesion: 1.0
Nodes (1): Email Sender Waterfall (SMTP2GO → Brevo → Mailgun)

### Community 63 - "Community 63"
Cohesion: 1.0
Nodes (1): FastAPI 0.115

### Community 64 - "Community 64"
Cohesion: 1.0
Nodes (1): Supabase Python Client

### Community 65 - "Community 65"
Cohesion: 1.0
Nodes (1): Stripe Metered Billing

### Community 66 - "Community 66"
Cohesion: 1.0
Nodes (1): Twilio Voice/SMS Integration

### Community 67 - "Community 67"
Cohesion: 1.0
Nodes (1): Google ADK + OpenRouter (AI Agent Pattern)

### Community 68 - "Community 68"
Cohesion: 1.0
Nodes (1): Google Cloud Run Deployment Target

### Community 69 - "Community 69"
Cohesion: 1.0
Nodes (1): TrustedForm TCPA Consent Integration

### Community 70 - "Community 70"
Cohesion: 1.0
Nodes (1): React 19 + Vite 6

### Community 71 - "Community 71"
Cohesion: 1.0
Nodes (1): Tailwind CSS 3

### Community 72 - "Community 72"
Cohesion: 1.0
Nodes (1): React Router v7

## Knowledge Gaps
- **134 isolated node(s):** `URAP Engine — E2E golden path test suite.  Tests the full request lifecycle agai`, `Synchronous httpx client for the full test session.`, `Email send should fail gracefully (not 500) when SMTP keys absent.`, `Warp Mode should complete (with fallback copy) even without AI keys.`, `SMS should be blocked by TCPA gate for unconsented lead.` (+129 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 18`** (9 nodes): `_FakeAsyncClient`, `.__aenter__()`, `.__aexit__()`, `.__init__()`, `.post()`, `_FakeResponse`, `.json()`, `test_domain_search_uses_current_prospeo_schema()`, `test_prospeo_client.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 21`** (4 nodes): `get_api_key()`, `URAP Engine — request auth middleware.  API key validation via X-Api-Key header.`, `require_api_key()`, `middleware.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 23`** (2 nodes): `Module VI — Security, Compliance & Trust: TCPA consent ledger.  Consent records`, `consent_ledger.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 25`** (2 nodes): `Contact Enrichment Waterfall`, `Hunter.io Email Enrichment`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 56`** (1 nodes): `Return all contact lists for this tenant (campaign lists + company lists merged)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 57`** (1 nodes): `Pull contacts at a domain via search-person + enrich in one pass.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 58`** (1 nodes): `urap-app — React + Vite Frontend Dashboard`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 59`** (1 nodes): `urap-engine — Python FastAPI Microservice`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 60`** (1 nodes): `@antigravity/urap-core — Express Middleware Plugin`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 61`** (1 nodes): `LeadStatusObject`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 62`** (1 nodes): `Email Sender Waterfall (SMTP2GO → Brevo → Mailgun)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 63`** (1 nodes): `FastAPI 0.115`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 64`** (1 nodes): `Supabase Python Client`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 65`** (1 nodes): `Stripe Metered Billing`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 66`** (1 nodes): `Twilio Voice/SMS Integration`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 67`** (1 nodes): `Google ADK + OpenRouter (AI Agent Pattern)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 68`** (1 nodes): `Google Cloud Run Deployment Target`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 69`** (1 nodes): `TrustedForm TCPA Consent Integration`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 70`** (1 nodes): `React 19 + Vite 6`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 71`** (1 nodes): `Tailwind CSS 3`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 72`** (1 nodes): `React Router v7`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `EnrichmentService` connect `Community 1` to `Community 3`, `Community 4`, `Community 5`, `Community 6`, `Community 10`, `Community 15`?**
  _High betweenness centrality (0.150) - this node is a cross-community bridge._
- **Why does `EmailSequenceService` connect `Community 4` to `Community 0`, `Community 1`, `Community 6`, `Community 7`, `Community 8`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._
- **Why does `ChannelStateMachine` connect `Community 1` to `Community 0`, `Community 4`, `Community 5`, `Community 6`, `Community 7`, `Community 14`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Are the 241 inferred relationships involving `EnrichmentService` (e.g. with `EnrichRequest` and `BulkEnrichRequest`) actually correct?**
  _`EnrichmentService` has 241 INFERRED edges - model-reasoned connections that need verification._
- **Are the 229 inferred relationships involving `WarpModeAgent` (e.g. with `EnrichRequest` and `BulkEnrichRequest`) actually correct?**
  _`WarpModeAgent` has 229 INFERRED edges - model-reasoned connections that need verification._
- **Are the 234 inferred relationships involving `EmailSequenceService` (e.g. with `EnrichRequest` and `BulkEnrichRequest`) actually correct?**
  _`EmailSequenceService` has 234 INFERRED edges - model-reasoned connections that need verification._
- **Are the 212 inferred relationships involving `ChannelStateMachine` (e.g. with `EnrichRequest` and `BulkEnrichRequest`) actually correct?**
  _`ChannelStateMachine` has 212 INFERRED edges - model-reasoned connections that need verification._