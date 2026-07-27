# Graph Report - urap  (2026-07-27)

## Corpus Check
- 91 files · ~206,386 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 844 nodes · 2913 edges · 37 communities detected
- Extraction: 34% EXTRACTED · 66% INFERRED · 0% AMBIGUOUS · INFERRED: 1933 edges (avg confidence: 0.52)
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
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
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

## God Nodes (most connected - your core abstractions)
1. `EnrichmentService` - 195 edges
2. `WarpModeAgent` - 184 edges
3. `EmailSequenceService` - 184 edges
4. `ChannelStateMachine` - 171 edges
5. `AutopilotRunner` - 158 edges
6. `ConsentLedgerService` - 156 edges
7. `BulkEnrichRunner` - 151 edges
8. `ReplyIntelligenceAgent` - 150 edges
9. `LeadRouterService` - 150 edges
10. `ApiKeyManager` - 147 edges

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
Cohesion: 0.1
Nodes (183): BaseModel, EnrichmentService, ChannelStateMachine, EmailSequenceService, ReplyIntelligenceAgent, Refine draft via Claude Sonnet. Returns (subject, body_html, was_reviewed)., Refine draft via Claude Sonnet. Returns (subject, body_html, was_reviewed)., Static template fallback when AI APIs are not configured. (+175 more)

### Community 1 - "Community 1"
Cohesion: 0.02
Nodes (133): Enum, _apollo_search(), _dedup_results(), _foursquare_search(), _google_places_search(), _hunter_domain(), _places_industry(), Company search — two modes:   1. Domain enrichment: domain provided → Hunter.io (+125 more)

### Community 2 - "Community 2"
Cohesion: 0.03
Nodes (31): fetchConfig(), fetchMarketplaces(), fetchSends(), handleRunNow(), handleToggle(), headers(), fetchJobs(), handleRun() (+23 more)

### Community 3 - "Community 3"
Cohesion: 0.05
Nodes (45): CleanlistClient, CleanlistResult, Cleanlist.ai email verification client — quality gate (all waterfall results pas, HunterClient, HunterResult, Hunter.io email enrichment client — domain sweep layer (waterfall layer 3 / bulk, Pull all publicly known emails at a domain., _build_contact() (+37 more)

### Community 4 - "Community 4"
Cohesion: 0.11
Nodes (15): BrevoClient, Brevo (formerly Sendinblue) email sender — overflow provider.  Free tier: ~9,000, SendResult, EmailSequence, Module II — Email sequence orchestrator.  Send waterfall: SMTP2GO (primary) → Br, Simple intent score from enrichment signals (0–100).         Full intent scoring, Send one email through the provider waterfall.         TCPA gate only blocks if, SendResult (+7 more)

### Community 5 - "Community 5"
Cohesion: 0.09
Nodes (17): AutopilotRunResult, build_outreach_html(), _db(), Autopilot runner — cron-triggered Warp Mode scheduler (Sprint 6 full implementat, Disable autopilot for a tenant., Return autopilot config for a tenant.          Falls back to the AUTOPILOT_CONFI, Execute one Autopilot cycle for a tenant.         Called by Cloud Scheduler (or, Add one explicit tracked CTA and the sender signature. (+9 more)

### Community 6 - "Community 6"
Cohesion: 0.08
Nodes (15): Module III — Warp Mode AI Copilot.  Given an ICP, autonomously:   1. Queries the, Refine draft via Claude Sonnet. Returns (subject, body_html, was_reviewed)., Static template fallback when AI APIs are not configured., Run a full Warp Mode job: enrich → generate copy → store → alert.          icp k, Return recent Warp Mode jobs for this tenant, newest first., Generate draft subject + body via Gemini Flash. Returns ("", "") on failure., WarpJobResult, WarpLead (+7 more)

### Community 7 - "Community 7"
Cohesion: 0.1
Nodes (18): ClaimResult, _db(), InboundLead, _infer_company_size(), _infer_title_level(), PreviewAttributes, Module IV — Inbound Lead Capture & Distribution (Sprint 5)., Step 1 of ping-post: receive inbound lead, enrich, store in Supabase.         Re (+10 more)

### Community 8 - "Community 8"
Cohesion: 0.08
Nodes (7): URAP Engine — E2E golden path test suite.  Tests the full request lifecycle agai, Email send should fail gracefully (not 500) when SMTP keys absent., Warp Mode should complete (with fallback copy) even without AI keys., SMS should be blocked by TCPA gate for unconsented lead., test_email_send_graceful_without_smtp_key(), test_sms_send_blocked_without_consent(), test_warp_mode_run()

### Community 9 - "Community 9"
Cohesion: 0.12
Nodes (16): create_discovery_call(), _get_service(), Tier 3 — Google Calendar: create discovery call events on meeting_set triggers., Create a 30-min discovery call event. Returns HTML link or '' on failure.      s, ParseResult, Module III — Reply Intelligence Agent.  Parses incoming reply text, classifies s, Heuristic fallback when Claude is not configured., Parse a reply, update channel state, fire alerts. Main agent method. (+8 more)

### Community 10 - "Community 10"
Cohesion: 0.13
Nodes (10): BidResult, _db(), RaceResult, Race Agents — CPL auction: simultaneous ping to all configured marketplaces, hig, Run CPL auction for each lead sequentially (avoids hammering marketplaces)., Return recent auction results + aggregate stats., Send auction ping to one marketplace. Returns CPL from response or config fallba, Pull all configured marketplace webhooks for this tenant + merge catalog names. (+2 more)

### Community 11 - "Community 11"
Cohesion: 0.13
Nodes (9): _db(), DispatchResult, Module IV — Marketplace Webhook Router (Phase 1 Route Core, BizReach integration, Upsert marketplace webhook config for a tenant., Dispatch a set of leads to a single target with a 3-attempt retry loop., Route selected leads to configured marketplace webhooks.         If ping_post=Tr, Return recent routing sessions for a tenant., Map URAP contact fields to the standardized marketplace payload schema. (+1 more)

### Community 12 - "Community 12"
Cohesion: 0.22
Nodes (5): _default_channel_state(), Module II — Omni-Channel Outreach: channel state machine.  Core rule: a reply on, Check if a channel is in a sendable state before queuing outreach., Advance to candidate only if it outranks current. Never downgrade., Call when a reply arrives on any channel.         Pauses all other channels, upg

### Community 13 - "Community 13"
Cohesion: 0.15
Nodes (7): BulkJob, _db(), Bulk enrichment runner — CSV list or ICP-filter batch jobs., Retrieve a bulk job record from Supabase., List recent bulk jobs for a tenant (summary only — no per-row results)., Enrich contacts from CSV text.         Expected columns (order-insensitive): fir, Bulk-enrich all contacts at a domain via the enrichment waterfall.         Wraps

### Community 14 - "Community 14"
Cohesion: 0.17
Nodes (14): _db(), delete_list(), get_list_items(), get_lists(), Lead list management — saves search results + enriched contacts to Supabase.  Ta, Create a named lead list and insert all items.     Each item dict may contain: n, Return all lists for a tenant, most recent first., Return all items in a specific list. (+6 more)

### Community 15 - "Community 15"
Cohesion: 0.23
Nodes (13): discover_contact(), _guess_domain_from_name(), _hunter_find(), _is_listing(), Contact discovery — two strategies in priority order:   1. Hunter.io domain sear, Discover contact info for a single business.     Returns: { email, first_name, l, Scrape the homepage for social media profile links., Fetch the real business website URL from Yelp's details endpoint. (+5 more)

### Community 16 - "Community 16"
Cohesion: 0.2
Nodes (3): getAllTools(), getToolsByPillar(), registerTool()

### Community 17 - "Community 17"
Cohesion: 0.22
Nodes (9): Antigravity / Dabblin Cloud Technologies, Multi-Tenant Design, URAP — Unified Revenue Acceleration Platform, URAP Sprint Roadmap (Sprints 0-9), Supabase Data Tables, URAP Full Logo (Dark Background), URAP Icon Logo, urap-logo.png (in-app asset) (+1 more)

### Community 18 - "Community 18"
Cohesion: 0.29
Nodes (3): Insert a consent record. Raises on DB error — caller must handle., Return True if at least one consent record exists for this lead., Return the most recent consent record for a lead, or None.

### Community 19 - "Community 19"
Cohesion: 0.5
Nodes (1): URAP Engine — request auth middleware.  API key validation via X-Api-Key header.

### Community 21 - "Community 21"
Cohesion: 1.0
Nodes (1): Module VI — Security, Compliance & Trust: TCPA consent ledger.  Consent records

### Community 23 - "Community 23"
Cohesion: 1.0
Nodes (2): Contact Enrichment Waterfall, Hunter.io Email Enrichment

### Community 53 - "Community 53"
Cohesion: 1.0
Nodes (1): urap-app — React + Vite Frontend Dashboard

### Community 54 - "Community 54"
Cohesion: 1.0
Nodes (1): urap-engine — Python FastAPI Microservice

### Community 55 - "Community 55"
Cohesion: 1.0
Nodes (1): @antigravity/urap-core — Express Middleware Plugin

### Community 56 - "Community 56"
Cohesion: 1.0
Nodes (1): LeadStatusObject

### Community 57 - "Community 57"
Cohesion: 1.0
Nodes (1): Email Sender Waterfall (SMTP2GO → Brevo → Mailgun)

### Community 58 - "Community 58"
Cohesion: 1.0
Nodes (1): FastAPI 0.115

### Community 59 - "Community 59"
Cohesion: 1.0
Nodes (1): Supabase Python Client

### Community 60 - "Community 60"
Cohesion: 1.0
Nodes (1): Stripe Metered Billing

### Community 61 - "Community 61"
Cohesion: 1.0
Nodes (1): Twilio Voice/SMS Integration

### Community 62 - "Community 62"
Cohesion: 1.0
Nodes (1): Google ADK + OpenRouter (AI Agent Pattern)

### Community 63 - "Community 63"
Cohesion: 1.0
Nodes (1): Google Cloud Run Deployment Target

### Community 64 - "Community 64"
Cohesion: 1.0
Nodes (1): TrustedForm TCPA Consent Integration

### Community 65 - "Community 65"
Cohesion: 1.0
Nodes (1): React 19 + Vite 6

### Community 66 - "Community 66"
Cohesion: 1.0
Nodes (1): Tailwind CSS 3

### Community 67 - "Community 67"
Cohesion: 1.0
Nodes (1): React Router v7

## Knowledge Gaps
- **122 isolated node(s):** `URAP Engine — E2E golden path test suite.  Tests the full request lifecycle agai`, `Synchronous httpx client for the full test session.`, `Email send should fail gracefully (not 500) when SMTP keys absent.`, `Warp Mode should complete (with fallback copy) even without AI keys.`, `SMS should be blocked by TCPA gate for unconsented lead.` (+117 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 19`** (4 nodes): `get_api_key()`, `URAP Engine — request auth middleware.  API key validation via X-Api-Key header.`, `require_api_key()`, `middleware.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 21`** (2 nodes): `Module VI — Security, Compliance & Trust: TCPA consent ledger.  Consent records`, `consent_ledger.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 23`** (2 nodes): `Contact Enrichment Waterfall`, `Hunter.io Email Enrichment`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 53`** (1 nodes): `urap-app — React + Vite Frontend Dashboard`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 54`** (1 nodes): `urap-engine — Python FastAPI Microservice`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 55`** (1 nodes): `@antigravity/urap-core — Express Middleware Plugin`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 56`** (1 nodes): `LeadStatusObject`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 57`** (1 nodes): `Email Sender Waterfall (SMTP2GO → Brevo → Mailgun)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 58`** (1 nodes): `FastAPI 0.115`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 59`** (1 nodes): `Supabase Python Client`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 60`** (1 nodes): `Stripe Metered Billing`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 61`** (1 nodes): `Twilio Voice/SMS Integration`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 62`** (1 nodes): `Google ADK + OpenRouter (AI Agent Pattern)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 63`** (1 nodes): `Google Cloud Run Deployment Target`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 64`** (1 nodes): `TrustedForm TCPA Consent Integration`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 65`** (1 nodes): `React 19 + Vite 6`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 66`** (1 nodes): `Tailwind CSS 3`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 67`** (1 nodes): `React Router v7`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `EnrichmentService` connect `Community 0` to `Community 3`, `Community 13`, `Community 6`, `Community 7`?**
  _High betweenness centrality (0.157) - this node is a cross-community bridge._
- **Why does `EmailSequenceService` connect `Community 0` to `Community 1`, `Community 4`, `Community 5`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **Why does `ChannelStateMachine` connect `Community 0` to `Community 9`, `Community 12`, `Community 4`, `Community 1`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Are the 187 inferred relationships involving `EnrichmentService` (e.g. with `EnrichRequest` and `BulkEnrichRequest`) actually correct?**
  _`EnrichmentService` has 187 INFERRED edges - model-reasoned connections that need verification._
- **Are the 175 inferred relationships involving `WarpModeAgent` (e.g. with `EnrichRequest` and `BulkEnrichRequest`) actually correct?**
  _`WarpModeAgent` has 175 INFERRED edges - model-reasoned connections that need verification._
- **Are the 180 inferred relationships involving `EmailSequenceService` (e.g. with `EnrichRequest` and `BulkEnrichRequest`) actually correct?**
  _`EmailSequenceService` has 180 INFERRED edges - model-reasoned connections that need verification._
- **Are the 158 inferred relationships involving `ChannelStateMachine` (e.g. with `EnrichRequest` and `BulkEnrichRequest`) actually correct?**
  _`ChannelStateMachine` has 158 INFERRED edges - model-reasoned connections that need verification._