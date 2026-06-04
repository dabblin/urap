# Graph Report - /Users/djdab/Developer/urap  (2026-06-02)

## Corpus Check
- 88 files · ~174,963 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 613 nodes · 1657 edges · 26 communities detected
- Extraction: 46% EXTRACTED · 54% INFERRED · 0% AMBIGUOUS · INFERRED: 899 edges (avg confidence: 0.53)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Core Service Registry|Core Service Registry]]
- [[_COMMUNITY_Contact Discovery & Lists|Contact Discovery & Lists]]
- [[_COMMUNITY_API Route Handlers|API Route Handlers]]
- [[_COMMUNITY_Cleanlist Email Verification|Cleanlist Email Verification]]
- [[_COMMUNITY_Product Architecture & Docs|Product Architecture & Docs]]
- [[_COMMUNITY_Brevo Email Sender|Brevo Email Sender]]
- [[_COMMUNITY_Frontend Prospector UI|Frontend Prospector UI]]
- [[_COMMUNITY_E2E Test Suite|E2E Test Suite]]
- [[_COMMUNITY_Inbound Lead Capture|Inbound Lead Capture]]
- [[_COMMUNITY_Reply Intelligence & Calendar|Reply Intelligence & Calendar]]
- [[_COMMUNITY_Channel State Machine|Channel State Machine]]
- [[_COMMUNITY_Autopilot Runner|Autopilot Runner]]
- [[_COMMUNITY_Company Search Engine|Company Search Engine]]
- [[_COMMUNITY_Warp Mode AI Copilot|Warp Mode AI Copilot]]
- [[_COMMUNITY_Bulk Enrichment Runner|Bulk Enrichment Runner]]
- [[_COMMUNITY_Contact Enrichment Waterfall|Contact Enrichment Waterfall]]
- [[_COMMUNITY_API Key Manager|API Key Manager]]
- [[_COMMUNITY_TCPA Consent Ledger|TCPA Consent Ledger]]
- [[_COMMUNITY_Bulk Enrich UI|Bulk Enrich UI]]
- [[_COMMUNITY_Autopilot UI|Autopilot UI]]
- [[_COMMUNITY_Integrations UI|Integrations UI]]
- [[_COMMUNITY_Auth Middleware|Auth Middleware]]
- [[_COMMUNITY_Consent Ledger Module|Consent Ledger Module]]
- [[_COMMUNITY_Module 57|Module 57]]
- [[_COMMUNITY_Module 58|Module 58]]
- [[_COMMUNITY_Module 59|Module 59]]

## God Nodes (most connected - your core abstractions)
1. `EnrichmentService` - 114 edges
2. `ChannelStateMachine` - 100 edges
3. `WarpModeAgent` - 91 edges
4. `EmailSequenceService` - 87 edges
5. `ConsentLedgerService` - 85 edges
6. `AutopilotRunner` - 80 edges
7. `BulkEnrichRunner` - 80 edges
8. `ReplyIntelligenceAgent` - 79 edges
9. `LeadRouterService` - 79 edges
10. `ApiKeyManager` - 76 edges

## Surprising Connections (you probably didn't know these)
- `URAP Full Logo (Dark Background)` --references--> `URAP Platform`  [INFERRED]
  urap-app/URAP Logo.png → README.md
- `Autopilot runner — cron-triggered Warp Mode scheduler (Sprint 6 full implementat` --uses--> `WarpModeAgent`  [INFERRED]
  urap-engine/modules/m5_api/autopilot_runner.py → urap-engine/modules/m3_agents/warp_mode.py
- `Save or update autopilot config for a tenant. Upsert on tenant_id.         sched` --uses--> `WarpModeAgent`  [INFERRED]
  urap-engine/modules/m5_api/autopilot_runner.py → urap-engine/modules/m3_agents/warp_mode.py
- `Disable autopilot for a tenant.` --uses--> `WarpModeAgent`  [INFERRED]
  urap-engine/modules/m5_api/autopilot_runner.py → urap-engine/modules/m3_agents/warp_mode.py
- `Return autopilot config for a tenant.` --uses--> `WarpModeAgent`  [INFERRED]
  urap-engine/modules/m5_api/autopilot_runner.py → urap-engine/modules/m3_agents/warp_mode.py

## Hyperedges (group relationships)
- **URAP Three-Component Plugin System** — urap_app_component, urap_engine_component, urap_core_component [EXTRACTED 1.00]
- **URAP Six Functional Modules** — m1_intelligence, m2_outreach, m3_agents, m4_inbound, m5_api, m6_compliance [EXTRACTED 1.00]
- **Email Sending Provider Waterfall** — email_sender_waterfall, tier3_integrations [EXTRACTED 1.00]
- **AI Agent Pipeline: Warp Mode + Reply Intelligence** — warp_mode, reply_intelligence, google_adk, google_calendar_tier3, telegram_tier3 [EXTRACTED 1.00]
- **TCPA Compliance Chain** — consent_ledger, trustedform, urap_core_component, m6_compliance [EXTRACTED 1.00]

## Communities

### Community 0 - "Core Service Registry"
Cohesion: 0.2
Nodes (83): BaseModel, EnrichmentService, ChannelStateMachine, EmailSequenceService, ReplyIntelligenceAgent, WarpModeAgent, LeadRouterService, Handles inbound lead capture, ping-post distribution, and Twilio geo-routing. (+75 more)

### Community 1 - "Contact Discovery & Lists"
Cohesion: 0.04
Nodes (58): discover_contacts_batch(), Enrich a batch. Each dict needs: index, name, domain, website, phone., _db(), delete_list(), get_list_items(), get_lists(), Lead list management — saves search results + enriched contacts to Supabase.  Ta, Create a named lead list and insert all items.     Each item dict may contain: n (+50 more)

### Community 2 - "API Route Handlers"
Cohesion: 0.05
Nodes (46): Enum, Pydantic 2.8, channel_event(), record_consent(), score_intent(), sms_send(), voice_dial(), voice_hangup() (+38 more)

### Community 3 - "Cleanlist Email Verification"
Cohesion: 0.07
Nodes (20): CleanlistClient, CleanlistResult, Cleanlist.ai email verification client — quality gate (all waterfall results pas, HunterClient, HunterResult, Hunter.io email enrichment client — domain sweep layer (waterfall layer 3 / bulk, Pull all publicly known emails at a domain., _build_contact() (+12 more)

### Community 4 - "Product Architecture & Docs"
Cohesion: 0.06
Nodes (45): Antigravity / Dabblin Cloud Technologies, Channel State Machine, Google Cloud Run Deployment Target, CompaniesSearch.tsx Page, TCPA Consent Ledger, Email Sender Waterfall (SMTP2GO → Brevo → Mailgun), Inbound Lead Capture Embed Script (embed.js), Contact Enrichment Waterfall (+37 more)

### Community 5 - "Brevo Email Sender"
Cohesion: 0.11
Nodes (15): BrevoClient, Brevo (formerly Sendinblue) email sender — overflow provider.  Free tier: ~9,000, SendResult, EmailSequence, Module II — Email sequence orchestrator.  Send waterfall: SMTP2GO (primary) → Br, Simple intent score from enrichment signals (0–100).         Full intent scoring, Send one email through the provider waterfall.         TCPA gate only blocks if, SendResult (+7 more)

### Community 6 - "Frontend Prospector UI"
Cohesion: 0.08
Nodes (3): getAllTools(), getToolsByPillar(), registerTool()

### Community 7 - "E2E Test Suite"
Cohesion: 0.08
Nodes (7): URAP Engine — E2E golden path test suite.  Tests the full request lifecycle agai, Email send should fail gracefully (not 500) when SMTP keys absent., Warp Mode should complete (with fallback copy) even without AI keys., SMS should be blocked by TCPA gate for unconsented lead., test_email_send_graceful_without_smtp_key(), test_sms_send_blocked_without_consent(), test_warp_mode_run()

### Community 8 - "Inbound Lead Capture"
Cohesion: 0.1
Nodes (18): ClaimResult, _db(), InboundLead, _infer_company_size(), _infer_title_level(), PreviewAttributes, Module IV — Inbound Lead Capture & Distribution (Sprint 5)., Step 1 of ping-post: receive inbound lead, enrich, store in Supabase.         Re (+10 more)

### Community 9 - "Reply Intelligence & Calendar"
Cohesion: 0.12
Nodes (16): create_discovery_call(), _get_service(), Tier 3 — Google Calendar: create discovery call events on meeting_set triggers., Create a 30-min discovery call event. Returns HTML link or '' on failure.      s, ParseResult, Module III — Reply Intelligence Agent.  Parses incoming reply text, classifies s, Heuristic fallback when Claude is not configured., Parse a reply, update channel state, fire alerts. Main agent method. (+8 more)

### Community 10 - "Channel State Machine"
Cohesion: 0.22
Nodes (5): _default_channel_state(), Module II — Omni-Channel Outreach: channel state machine.  Core rule: a reply on, Check if a channel is in a sendable state before queuing outreach., Advance to candidate only if it outranks current. Never downgrade., Call when a reply arrives on any channel.         Pauses all other channels, upg

### Community 11 - "Autopilot Runner"
Cohesion: 0.15
Nodes (9): AutopilotRunResult, _db(), Autopilot runner — cron-triggered Warp Mode scheduler (Sprint 6 full implementat, Compute unsubscribe rate = unsubscribed / total leads in last 7 days., Count sequences queued today for throttle check., Save or update autopilot config for a tenant. Upsert on tenant_id.         sched, Disable autopilot for a tenant., Return autopilot config for a tenant. (+1 more)

### Community 12 - "Company Search Engine"
Cohesion: 0.2
Nodes (14): _apollo_search(), _dedup_results(), _foursquare_search(), _google_places_search(), _hunter_domain(), _places_industry(), Company search — two modes:   1. Domain enrichment: domain provided → Hunter.io, Merge results from multiple sources, dedup by phone or name+location. (+6 more)

### Community 13 - "Warp Mode AI Copilot"
Cohesion: 0.13
Nodes (8): Module III — Warp Mode AI Copilot.  Given an ICP, autonomously:   1. Queries the, Refine draft via Claude Sonnet. Returns (subject, body_html, was_reviewed)., Static template fallback when AI APIs are not configured., Run a full Warp Mode job: enrich → generate copy → store → alert.          icp k, Return recent Warp Mode jobs for this tenant, newest first., Generate draft subject + body via Gemini Flash. Returns ("", "") on failure., WarpJobResult, WarpLead

### Community 14 - "Bulk Enrichment Runner"
Cohesion: 0.15
Nodes (7): BulkJob, _db(), Bulk enrichment runner — CSV list or ICP-filter batch jobs., Retrieve a bulk job record from Supabase., List recent bulk jobs for a tenant (summary only — no per-row results)., Enrich contacts from CSV text.         Expected columns (order-insensitive): fir, Bulk-enrich all contacts at a domain via the enrichment waterfall.         Wraps

### Community 15 - "Contact Enrichment Waterfall"
Cohesion: 0.23
Nodes (13): discover_contact(), _guess_domain_from_name(), _hunter_find(), _is_listing(), Contact discovery — two strategies in priority order:   1. Hunter.io domain sear, Discover contact info for a single business.     Returns: { email, first_name, l, Scrape the homepage for social media profile links., Fetch the real business website URL from Yelp's details endpoint. (+5 more)

### Community 16 - "API Key Manager"
Cohesion: 0.2
Nodes (7): _db(), _hash(), Tenant developer API key management — generate, list, revoke., Revoke (soft-delete) an API key., Generate a new API key for a tenant.         The plaintext key is returned ONCE, Validate an incoming API key. Returns the tenant record or None.         Updates, List all API keys for a tenant (prefix + metadata only — no hash exposed).

### Community 17 - "TCPA Consent Ledger"
Cohesion: 0.29
Nodes (3): Insert a consent record. Raises on DB error — caller must handle., Return True if at least one consent record exists for this lead., Return the most recent consent record for a lead, or None.

### Community 19 - "Bulk Enrich UI"
Cohesion: 0.8
Nodes (4): fetchJobs(), handleRun(), headers(), loadJob()

### Community 20 - "Autopilot UI"
Cohesion: 0.8
Nodes (4): fetchConfig(), handleRunNow(), handleToggle(), headers()

### Community 21 - "Integrations UI"
Cohesion: 0.8
Nodes (4): fetchWebhooks(), handleDelete(), handleSubscribe(), headers()

### Community 22 - "Auth Middleware"
Cohesion: 0.5
Nodes (1): URAP Engine — request auth middleware.  API key validation via X-Api-Key header.

### Community 28 - "Consent Ledger Module"
Cohesion: 1.0
Nodes (1): Module VI — Security, Compliance & Trust: TCPA consent ledger.  Consent records

### Community 57 - "Module 57"
Cohesion: 1.0
Nodes (1): urap-app — React + Vite Frontend Dashboard

### Community 58 - "Module 58"
Cohesion: 1.0
Nodes (1): urap-engine — Python FastAPI Microservice

### Community 59 - "Module 59"
Cohesion: 1.0
Nodes (1): @antigravity/urap-core — Express Middleware Plugin

## Knowledge Gaps
- **83 isolated node(s):** `URAP Engine — E2E golden path test suite.  Tests the full request lifecycle agai`, `Synchronous httpx client for the full test session.`, `Email send should fail gracefully (not 500) when SMTP keys absent.`, `Warp Mode should complete (with fallback copy) even without AI keys.`, `SMS should be blocked by TCPA gate for unconsented lead.` (+78 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Auth Middleware`** (4 nodes): `get_api_key()`, `URAP Engine — request auth middleware.  API key validation via X-Api-Key header.`, `require_api_key()`, `middleware.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Consent Ledger Module`** (2 nodes): `Module VI — Security, Compliance & Trust: TCPA consent ledger.  Consent records`, `consent_ledger.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Module 57`** (1 nodes): `urap-app — React + Vite Frontend Dashboard`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Module 58`** (1 nodes): `urap-engine — Python FastAPI Microservice`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Module 59`** (1 nodes): `@antigravity/urap-core — Express Middleware Plugin`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `EnrichmentService` connect `Core Service Registry` to `Inbound Lead Capture`, `Cleanlist Email Verification`, `Warp Mode AI Copilot`, `Bulk Enrichment Runner`?**
  _High betweenness centrality (0.167) - this node is a cross-community bridge._
- **Why does `Pydantic 2.8` connect `API Route Handlers` to `Contact Discovery & Lists`, `Product Architecture & Docs`?**
  _High betweenness centrality (0.116) - this node is a cross-community bridge._
- **Why does `urap-engine (FastAPI Microservice)` connect `Product Architecture & Docs` to `API Route Handlers`?**
  _High betweenness centrality (0.115) - this node is a cross-community bridge._
- **Are the 107 inferred relationships involving `EnrichmentService` (e.g. with `EnrichRequest` and `BulkEnrichRequest`) actually correct?**
  _`EnrichmentService` has 107 INFERRED edges - model-reasoned connections that need verification._
- **Are the 87 inferred relationships involving `ChannelStateMachine` (e.g. with `EnrichRequest` and `BulkEnrichRequest`) actually correct?**
  _`ChannelStateMachine` has 87 INFERRED edges - model-reasoned connections that need verification._
- **Are the 82 inferred relationships involving `WarpModeAgent` (e.g. with `EnrichRequest` and `BulkEnrichRequest`) actually correct?**
  _`WarpModeAgent` has 82 INFERRED edges - model-reasoned connections that need verification._
- **Are the 83 inferred relationships involving `EmailSequenceService` (e.g. with `EnrichRequest` and `BulkEnrichRequest`) actually correct?**
  _`EmailSequenceService` has 83 INFERRED edges - model-reasoned connections that need verification._