# Graph Report - urap  (2026-07-24)

## Corpus Check
- 91 files · ~206,033 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 827 nodes · 2871 edges · 65 communities detected
- Extraction: 34% EXTRACTED · 66% INFERRED · 0% AMBIGUOUS · INFERRED: 1895 edges (avg confidence: 0.52)
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
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 81|Community 81]]
- [[_COMMUNITY_Community 82|Community 82]]
- [[_COMMUNITY_Community 83|Community 83]]
- [[_COMMUNITY_Community 84|Community 84]]
- [[_COMMUNITY_Community 85|Community 85]]
- [[_COMMUNITY_Community 86|Community 86]]
- [[_COMMUNITY_Community 87|Community 87]]
- [[_COMMUNITY_Community 88|Community 88]]
- [[_COMMUNITY_Community 89|Community 89]]
- [[_COMMUNITY_Community 90|Community 90]]
- [[_COMMUNITY_Community 91|Community 91]]
- [[_COMMUNITY_Community 92|Community 92]]
- [[_COMMUNITY_Community 93|Community 93]]
- [[_COMMUNITY_Community 94|Community 94]]
- [[_COMMUNITY_Community 95|Community 95]]

## God Nodes (most connected - your core abstractions)
1. `EnrichmentService` - 191 edges
2. `WarpModeAgent` - 173 edges
3. `EmailSequenceService` - 173 edges
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
Cohesion: 0.15
Nodes (93): EnrichmentService, ChannelStateMachine, EmailSequenceService, ReplyIntelligenceAgent, Refine draft via Claude Sonnet. Returns (subject, body_html, was_reviewed)., Static template fallback when AI APIs are not configured., Run a full Warp Mode job: enrich → generate copy → store → alert.          icp k, Return recent Warp Mode jobs for this tenant, newest first. (+85 more)

### Community 1 - "Community 1"
Cohesion: 0.03
Nodes (31): fetchConfig(), fetchMarketplaces(), fetchSends(), handleRunNow(), handleToggle(), headers(), fetchJobs(), handleRun() (+23 more)

### Community 2 - "Community 2"
Cohesion: 0.03
Nodes (66): Enum, dispatch(), dispatch_stream(), _haiku_opener(), Module II — Campaign dispatcher with AI personalization.  Batch-sends a campaign, Dispatch campaign to all contacts and yield progress events as NDJSON., Dispatch campaign to all contacts. Returns {sent, failed, skipped}., _render() (+58 more)

### Community 3 - "Community 3"
Cohesion: 0.05
Nodes (46): CleanlistClient, CleanlistResult, Cleanlist.ai email verification client — quality gate (all waterfall results pas, HunterClient, HunterResult, Hunter.io email enrichment client — domain sweep layer (waterfall layer 3 / bulk, Pull all publicly known emails at a domain., _build_contact() (+38 more)

### Community 4 - "Community 4"
Cohesion: 0.12
Nodes (44): BaseModel, MarketplaceRouter, Routes enriched URAP contacts to external buyer marketplace webhooks., RaceAuction, CPL auction engine. Pings all configured marketplaces simultaneously,     picks, ApiKeyCreateRequest, AutopilotConfigRequest, BulkEnrichCsvRequest (+36 more)

### Community 5 - "Community 5"
Cohesion: 0.05
Nodes (31): create_discovery_call(), _get_service(), Tier 3 — Google Calendar: create discovery call events on meeting_set triggers., Create a 30-min discovery call event. Returns HTML link or '' on failure.      s, ParseResult, Module III — Reply Intelligence Agent.  Parses incoming reply text, classifies s, Heuristic fallback when Claude is not configured., Parse a reply, update channel state, fire alerts. Main agent method. (+23 more)

### Community 6 - "Community 6"
Cohesion: 0.08
Nodes (32): _apollo_search(), _dedup_results(), _foursquare_search(), _google_places_search(), _hunter_domain(), _places_industry(), Company search — two modes:   1. Domain enrichment: domain provided → Hunter.io, Merge results from multiple sources, dedup by phone or name+location. (+24 more)

### Community 7 - "Community 7"
Cohesion: 0.11
Nodes (15): BrevoClient, Brevo (formerly Sendinblue) email sender — overflow provider.  Free tier: ~9,000, SendResult, EmailSequence, Module II — Email sequence orchestrator.  Send waterfall: SMTP2GO (primary) → Br, Simple intent score from enrichment signals (0–100).         Full intent scoring, Send one email through the provider waterfall.         TCPA gate only blocks if, SendResult (+7 more)

### Community 8 - "Community 8"
Cohesion: 0.08
Nodes (7): URAP Engine — E2E golden path test suite.  Tests the full request lifecycle agai, Email send should fail gracefully (not 500) when SMTP keys absent., Warp Mode should complete (with fallback copy) even without AI keys., SMS should be blocked by TCPA gate for unconsented lead., test_email_send_graceful_without_smtp_key(), test_sms_send_blocked_without_consent(), test_warp_mode_run()

### Community 9 - "Community 9"
Cohesion: 0.1
Nodes (18): ClaimResult, _db(), InboundLead, _infer_company_size(), _infer_title_level(), PreviewAttributes, Module IV — Inbound Lead Capture & Distribution (Sprint 5)., Step 1 of ping-post: receive inbound lead, enrich, store in Supabase.         Re (+10 more)

### Community 10 - "Community 10"
Cohesion: 0.13
Nodes (11): AutopilotRunResult, _db(), Autopilot runner — cron-triggered Warp Mode scheduler (Sprint 6 full implementat, Execute one Autopilot cycle for a tenant.         Called by Cloud Scheduler (or, Drop leads already emailed in the trailing 90 days or unsubscribed., Send warp-generated copy via the provider waterfall; record a real         campa, Pull recently enriched contacts above min_score for route-after-warp dispatch., Compute unsubscribe rate = unsubscribed / total leads in last 7 days. (+3 more)

### Community 11 - "Community 11"
Cohesion: 0.13
Nodes (10): BidResult, _db(), RaceResult, Race Agents — CPL auction: simultaneous ping to all configured marketplaces, hig, Run CPL auction for each lead sequentially (avoids hammering marketplaces)., Return recent auction results + aggregate stats., Send auction ping to one marketplace. Returns CPL from response or config fallba, Pull all configured marketplace webhooks for this tenant + merge catalog names. (+2 more)

### Community 12 - "Community 12"
Cohesion: 0.13
Nodes (18): create_sequence(), _db(), enroll_contact(), get_sequences(), Drip sequence orchestrator — create templates, enroll contacts, fire due steps., Update enrollment status — called by Brevo webhook on reply/bounce/unsub., Find active enrollments whose next_send_at <= now, send the current step,     th, Save a reusable sequence template.     Returns: { sequence_id, name, step_count (+10 more)

### Community 13 - "Community 13"
Cohesion: 0.11
Nodes (17): WarpModeAgent, Compute unsubscribe rate = unsubscribed / total leads in last 7 days., Count sequences queued today for throttle check., Save or update autopilot config for a tenant. Upsert on tenant_id.         sched, Disable autopilot for a tenant., Return autopilot config for a tenant., Execute one Autopilot cycle for a tenant.         Called by Cloud Scheduler (or, campaign_stats() (+9 more)

### Community 14 - "Community 14"
Cohesion: 0.13
Nodes (9): _db(), DispatchResult, Module IV — Marketplace Webhook Router (Phase 1 Route Core, BizReach integration, Upsert marketplace webhook config for a tenant., Dispatch a set of leads to a single target with a 3-attempt retry loop., Route selected leads to configured marketplace webhooks.         If ping_post=Tr, Return recent routing sessions for a tenant., Map URAP contact fields to the standardized marketplace payload schema. (+1 more)

### Community 15 - "Community 15"
Cohesion: 0.22
Nodes (5): _default_channel_state(), Module II — Omni-Channel Outreach: channel state machine.  Core rule: a reply on, Check if a channel is in a sendable state before queuing outreach., Advance to candidate only if it outranks current. Never downgrade., Call when a reply arrives on any channel.         Pauses all other channels, upg

### Community 16 - "Community 16"
Cohesion: 0.17
Nodes (14): _db(), delete_list(), get_list_items(), get_lists(), Lead list management — saves search results + enriched contacts to Supabase.  Ta, Create a named lead list and insert all items.     Each item dict may contain: n, Return all lists for a tenant, most recent first., Return all items in a specific list. (+6 more)

### Community 17 - "Community 17"
Cohesion: 0.2
Nodes (3): getAllTools(), getToolsByPillar(), registerTool()

### Community 18 - "Community 18"
Cohesion: 0.22
Nodes (9): Antigravity / Dabblin Cloud Technologies, Multi-Tenant Design, URAP — Unified Revenue Acceleration Platform, URAP Sprint Roadmap (Sprints 0-9), Supabase Data Tables, URAP Full Logo (Dark Background), URAP Icon Logo, urap-logo.png (in-app asset) (+1 more)

### Community 19 - "Community 19"
Cohesion: 0.29
Nodes (3): Insert a consent record. Raises on DB error — caller must handle., Return True if at least one consent record exists for this lead., Return the most recent consent record for a lead, or None.

### Community 20 - "Community 20"
Cohesion: 0.5
Nodes (1): URAP Engine — request auth middleware.  API key validation via X-Api-Key header.

### Community 21 - "Community 21"
Cohesion: 0.67
Nodes (2): test_multisector_run_sources_and_keeps_every_sector(), test_warp_mode_accepts_batches_larger_than_25()

### Community 23 - "Community 23"
Cohesion: 1.0
Nodes (2): autopilot_config(), Return current Autopilot config for this tenant.

### Community 24 - "Community 24"
Cohesion: 1.0
Nodes (2): capture_lead(), Step 1 — Inbound lead capture. Enriches, geo-locates, stores in urap_lead_distri

### Community 25 - "Community 25"
Cohesion: 1.0
Nodes (2): Launch a Warp Mode job: ICP → enrich → AI copy → queue.     Gemini Flash drafts,, warp_run()

### Community 26 - "Community 26"
Cohesion: 1.0
Nodes (2): get_bulk_job(), Retrieve a bulk job record by ID.

### Community 27 - "Community 27"
Cohesion: 1.0
Nodes (2): List recent Warp Mode jobs for this tenant., warp_jobs()

### Community 28 - "Community 28"
Cohesion: 1.0
Nodes (2): race_results(), Return recent CPL auction results + aggregate stats for this tenant.

### Community 29 - "Community 29"
Cohesion: 1.0
Nodes (2): Save or update webhook URL, API key, and CPL target for a marketplace., route_save_marketplace()

### Community 30 - "Community 30"
Cohesion: 1.0
Nodes (2): create_api_key(), Generate a new developer API key. Plaintext returned once — store immediately.

### Community 31 - "Community 31"
Cohesion: 1.0
Nodes (2): autopilot_run(), Trigger one Autopilot cycle manually (or via Cloud Scheduler cron).     Runs War

### Community 32 - "Community 32"
Cohesion: 1.0
Nodes (2): Parse an incoming reply: classify sentiment, update channel state, fire alerts., reply_parse()

### Community 33 - "Community 33"
Cohesion: 1.0
Nodes (2): bulk_enrich_icp(), Run a bulk enrichment job for all contacts at a domain.

### Community 34 - "Community 34"
Cohesion: 1.0
Nodes (2): bulk_enrich_csv(), Run a bulk enrichment job from CSV text. Columns: first_name, last_name, domain/

### Community 35 - "Community 35"
Cohesion: 1.0
Nodes (2): Revoke a developer API key., revoke_api_key()

### Community 36 - "Community 36"
Cohesion: 1.0
Nodes (2): autopilot_enable(), Enable Autopilot and save ICP config + schedule for this tenant.

### Community 37 - "Community 37"
Cohesion: 1.0
Nodes (2): Return all 18 marketplace catalog entries merged with tenant webhook configs., route_get_marketplaces()

### Community 38 - "Community 38"
Cohesion: 1.0
Nodes (2): List recently captured leads for this tenant (no PII in listing)., recent_leads()

### Community 39 - "Community 39"
Cohesion: 1.0
Nodes (2): Send a single email through the SMTP2GO → Brevo → Mailgun waterfall., send_email()

### Community 40 - "Community 40"
Cohesion: 1.0
Nodes (2): create_sequence(), Create a reusable drip sequence template.

### Community 41 - "Community 41"
Cohesion: 1.0
Nodes (2): get_lead_preview(), Step 2 — Ping-post preview. Returns anonymized attributes for buyer evaluation.

### Community 42 - "Community 42"
Cohesion: 1.0
Nodes (2): get_campaign_page_public(), Public — fetched by the dabblin-landing-pages Next.js app at render time.

### Community 43 - "Community 43"
Cohesion: 1.0
Nodes (2): claim_lead(), Step 3 — Ping-post claim. Releases full PII to buyer, fires Stripe metered event

### Community 44 - "Community 44"
Cohesion: 1.0
Nodes (2): generate_templates(), Generate cold email template subject + HTML body using Gemini Flash based on lis

### Community 45 - "Community 45"
Cohesion: 1.0
Nodes (2): autopilot_disable(), Disable Autopilot for this tenant.

### Community 46 - "Community 46"
Cohesion: 1.0
Nodes (2): list_bulk_jobs(), List recent bulk enrichment jobs for this tenant.

### Community 47 - "Community 47"
Cohesion: 1.0
Nodes (2): race_run(), Run CPL auction across all configured marketplaces.     Pings all simultaneously

### Community 48 - "Community 48"
Cohesion: 1.0
Nodes (2): get_campaign_lists(), Return all contact lists for this tenant (campaign lists + company lists merged)

### Community 49 - "Community 49"
Cohesion: 1.0
Nodes (1): Module VI — Security, Compliance & Trust: TCPA consent ledger.  Consent records

### Community 51 - "Community 51"
Cohesion: 1.0
Nodes (2): Contact Enrichment Waterfall, Hunter.io Email Enrichment

### Community 81 - "Community 81"
Cohesion: 1.0
Nodes (1): urap-app — React + Vite Frontend Dashboard

### Community 82 - "Community 82"
Cohesion: 1.0
Nodes (1): urap-engine — Python FastAPI Microservice

### Community 83 - "Community 83"
Cohesion: 1.0
Nodes (1): @antigravity/urap-core — Express Middleware Plugin

### Community 84 - "Community 84"
Cohesion: 1.0
Nodes (1): LeadStatusObject

### Community 85 - "Community 85"
Cohesion: 1.0
Nodes (1): Email Sender Waterfall (SMTP2GO → Brevo → Mailgun)

### Community 86 - "Community 86"
Cohesion: 1.0
Nodes (1): FastAPI 0.115

### Community 87 - "Community 87"
Cohesion: 1.0
Nodes (1): Supabase Python Client

### Community 88 - "Community 88"
Cohesion: 1.0
Nodes (1): Stripe Metered Billing

### Community 89 - "Community 89"
Cohesion: 1.0
Nodes (1): Twilio Voice/SMS Integration

### Community 90 - "Community 90"
Cohesion: 1.0
Nodes (1): Google ADK + OpenRouter (AI Agent Pattern)

### Community 91 - "Community 91"
Cohesion: 1.0
Nodes (1): Google Cloud Run Deployment Target

### Community 92 - "Community 92"
Cohesion: 1.0
Nodes (1): TrustedForm TCPA Consent Integration

### Community 93 - "Community 93"
Cohesion: 1.0
Nodes (1): React 19 + Vite 6

### Community 94 - "Community 94"
Cohesion: 1.0
Nodes (1): Tailwind CSS 3

### Community 95 - "Community 95"
Cohesion: 1.0
Nodes (1): React Router v7

## Knowledge Gaps
- **118 isolated node(s):** `URAP Engine — E2E golden path test suite.  Tests the full request lifecycle agai`, `Synchronous httpx client for the full test session.`, `Email send should fail gracefully (not 500) when SMTP keys absent.`, `Warp Mode should complete (with fallback copy) even without AI keys.`, `SMS should be blocked by TCPA gate for unconsented lead.` (+113 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 20`** (4 nodes): `get_api_key()`, `URAP Engine — request auth middleware.  API key validation via X-Api-Key header.`, `require_api_key()`, `middleware.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 21`** (3 nodes): `test_multisector_run_sources_and_keeps_every_sector()`, `test_warp_mode_accepts_batches_larger_than_25()`, `test_autopilot_multisector.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 23`** (2 nodes): `autopilot_config()`, `Return current Autopilot config for this tenant.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 24`** (2 nodes): `capture_lead()`, `Step 1 — Inbound lead capture. Enriches, geo-locates, stores in urap_lead_distri`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 25`** (2 nodes): `Launch a Warp Mode job: ICP → enrich → AI copy → queue.     Gemini Flash drafts,`, `warp_run()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 26`** (2 nodes): `get_bulk_job()`, `Retrieve a bulk job record by ID.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 27`** (2 nodes): `List recent Warp Mode jobs for this tenant.`, `warp_jobs()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 28`** (2 nodes): `race_results()`, `Return recent CPL auction results + aggregate stats for this tenant.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 29`** (2 nodes): `Save or update webhook URL, API key, and CPL target for a marketplace.`, `route_save_marketplace()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 30`** (2 nodes): `create_api_key()`, `Generate a new developer API key. Plaintext returned once — store immediately.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 31`** (2 nodes): `autopilot_run()`, `Trigger one Autopilot cycle manually (or via Cloud Scheduler cron).     Runs War`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 32`** (2 nodes): `Parse an incoming reply: classify sentiment, update channel state, fire alerts.`, `reply_parse()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 33`** (2 nodes): `bulk_enrich_icp()`, `Run a bulk enrichment job for all contacts at a domain.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 34`** (2 nodes): `bulk_enrich_csv()`, `Run a bulk enrichment job from CSV text. Columns: first_name, last_name, domain/`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 35`** (2 nodes): `Revoke a developer API key.`, `revoke_api_key()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 36`** (2 nodes): `autopilot_enable()`, `Enable Autopilot and save ICP config + schedule for this tenant.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 37`** (2 nodes): `Return all 18 marketplace catalog entries merged with tenant webhook configs.`, `route_get_marketplaces()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 38`** (2 nodes): `List recently captured leads for this tenant (no PII in listing).`, `recent_leads()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 39`** (2 nodes): `Send a single email through the SMTP2GO → Brevo → Mailgun waterfall.`, `send_email()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 40`** (2 nodes): `create_sequence()`, `Create a reusable drip sequence template.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 41`** (2 nodes): `get_lead_preview()`, `Step 2 — Ping-post preview. Returns anonymized attributes for buyer evaluation.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 42`** (2 nodes): `get_campaign_page_public()`, `Public — fetched by the dabblin-landing-pages Next.js app at render time.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 43`** (2 nodes): `claim_lead()`, `Step 3 — Ping-post claim. Releases full PII to buyer, fires Stripe metered event`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 44`** (2 nodes): `generate_templates()`, `Generate cold email template subject + HTML body using Gemini Flash based on lis`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 45`** (2 nodes): `autopilot_disable()`, `Disable Autopilot for this tenant.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 46`** (2 nodes): `list_bulk_jobs()`, `List recent bulk enrichment jobs for this tenant.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 47`** (2 nodes): `race_run()`, `Run CPL auction across all configured marketplaces.     Pings all simultaneously`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 48`** (2 nodes): `get_campaign_lists()`, `Return all contact lists for this tenant (campaign lists + company lists merged)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 49`** (2 nodes): `Module VI — Security, Compliance & Trust: TCPA consent ledger.  Consent records`, `consent_ledger.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 51`** (2 nodes): `Contact Enrichment Waterfall`, `Hunter.io Email Enrichment`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 81`** (1 nodes): `urap-app — React + Vite Frontend Dashboard`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 82`** (1 nodes): `urap-engine — Python FastAPI Microservice`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 83`** (1 nodes): `@antigravity/urap-core — Express Middleware Plugin`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 84`** (1 nodes): `LeadStatusObject`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 85`** (1 nodes): `Email Sender Waterfall (SMTP2GO → Brevo → Mailgun)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 86`** (1 nodes): `FastAPI 0.115`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 87`** (1 nodes): `Supabase Python Client`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 88`** (1 nodes): `Stripe Metered Billing`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 89`** (1 nodes): `Twilio Voice/SMS Integration`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 90`** (1 nodes): `Google ADK + OpenRouter (AI Agent Pattern)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 91`** (1 nodes): `Google Cloud Run Deployment Target`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 92`** (1 nodes): `TrustedForm TCPA Consent Integration`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 93`** (1 nodes): `React 19 + Vite 6`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 94`** (1 nodes): `Tailwind CSS 3`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 95`** (1 nodes): `React Router v7`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `EnrichmentService` connect `Community 0` to `Community 2`, `Community 3`, `Community 4`, `Community 5`, `Community 9`, `Community 13`, `Community 23`, `Community 24`, `Community 25`, `Community 26`, `Community 27`, `Community 28`, `Community 29`, `Community 30`, `Community 31`, `Community 32`, `Community 33`, `Community 34`, `Community 35`, `Community 36`, `Community 37`, `Community 38`, `Community 39`, `Community 40`, `Community 41`, `Community 42`, `Community 43`, `Community 44`, `Community 45`, `Community 46`, `Community 47`?**
  _High betweenness centrality (0.152) - this node is a cross-community bridge._
- **Why does `EmailSequenceService` connect `Community 0` to `Community 2`, `Community 4`, `Community 6`, `Community 7`, `Community 10`, `Community 12`, `Community 13`, `Community 23`, `Community 24`, `Community 25`, `Community 26`, `Community 27`, `Community 28`, `Community 29`, `Community 30`, `Community 31`, `Community 32`, `Community 33`, `Community 34`, `Community 35`, `Community 36`, `Community 37`, `Community 38`, `Community 39`, `Community 40`, `Community 41`, `Community 42`, `Community 43`, `Community 44`, `Community 45`, `Community 46`, `Community 47`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Why does `ChannelStateMachine` connect `Community 0` to `Community 4`, `Community 5`, `Community 7`, `Community 12`, `Community 13`, `Community 15`, `Community 23`, `Community 24`, `Community 25`, `Community 26`, `Community 27`, `Community 28`, `Community 29`, `Community 30`, `Community 31`, `Community 32`, `Community 33`, `Community 34`, `Community 35`, `Community 36`, `Community 37`, `Community 38`, `Community 39`, `Community 40`, `Community 41`, `Community 42`, `Community 43`, `Community 44`, `Community 45`, `Community 46`, `Community 47`?**
  _High betweenness centrality (0.056) - this node is a cross-community bridge._
- **Are the 183 inferred relationships involving `EnrichmentService` (e.g. with `EnrichRequest` and `BulkEnrichRequest`) actually correct?**
  _`EnrichmentService` has 183 INFERRED edges - model-reasoned connections that need verification._
- **Are the 164 inferred relationships involving `WarpModeAgent` (e.g. with `EnrichRequest` and `BulkEnrichRequest`) actually correct?**
  _`WarpModeAgent` has 164 INFERRED edges - model-reasoned connections that need verification._
- **Are the 169 inferred relationships involving `EmailSequenceService` (e.g. with `EnrichRequest` and `BulkEnrichRequest`) actually correct?**
  _`EmailSequenceService` has 169 INFERRED edges - model-reasoned connections that need verification._
- **Are the 158 inferred relationships involving `ChannelStateMachine` (e.g. with `EnrichRequest` and `BulkEnrichRequest`) actually correct?**
  _`ChannelStateMachine` has 158 INFERRED edges - model-reasoned connections that need verification._