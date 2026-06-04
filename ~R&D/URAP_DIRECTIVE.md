# URAP — Software Directive

**Maintained by:** Antigravity / Dabblin Cloud Technologies  
**CIO:** Dennis Day II  
**Document type:** Standing R&D Directive — append-only history, versioned by date

---

## What Is URAP?

URAP (Unified Revenue Acceleration Platform) is a three-component SaaS system for outbound prospecting, lead enrichment, omni-channel outreach, and lead monetization:

| Component | Tech | Role |
|---|---|---|
| `urap-app` | React + Vite + Tailwind | Admin dashboard UI |
| `urap-engine` | Python FastAPI | Core AI + enrichment + routing engine |
| `urap-core` | Express middleware | Tenant plugin / embed layer |

**God Nodes** (highest-connectivity abstractions — touch these carefully):
1. `EnrichmentService` — contact data waterfall (Hunter → Apollo → Foursquare → Cleanlist)
2. `ChannelStateMachine` — omni-channel outreach state (email, SMS, voice)
3. `WarpModeAgent` — AI copilot: enrich + generate copy + route autonomously
4. `EmailSequenceService` — SMTP2GO → Brevo → Mailgun waterfall
5. `ConsentLedgerService` — TCPA compliance gate (blocks outreach without consent record)
6. `AutopilotRunner` — cron-triggered Warp Mode + routing scheduler
7. `BulkEnrichRunner` — CSV and ICP-filter batch enrichment jobs
8. `ReplyIntelligenceAgent` — incoming reply parser + calendar event creator
9. `LeadRouterService` — ping-post lead distribution + Stripe metered billing
10. `ApiKeyManager` — tenant API key generation + validation

**Six functional modules (urap-engine):**
- `m1_intelligence` — enrichment waterfall
- `m2_outreach` — email sequencer + channel state machine
- `m3_agents` — Warp Mode + Reply Intelligence
- `m4_inbound` — inbound lead capture + lead router + marketplace dispatch
- `m5_api` — FastAPI route handlers + autopilot runner
- `m6_compliance` — TCPA consent ledger

---

## Strategic Partnership: BizReach Pro (Kenny's App)

BizReach Pro is a lead generation command center built by Coalescent Mind. Antigravity/Dabblin Cloud Technologies has a technical partnership to integrate BizReach Pro's monetization infrastructure into URAP.

**Partnership model:**
- BizReach Pro = lead generation supply side (Finder, Campaigns, Funnels, Outreach)
- URAP = lead enrichment, qualification, routing, and monetization layer
- The two platforms share a standardized webhook payload schema (see Payload Contract below)
- BizReach's NetNavis Relay Pipeline (ElecMan.EXE → Route → Bass.EXE) maps directly to URAP's `AutopilotRunner → marketplace_router → race_agents` chain

**R&D intake:** When Kenny ships new tab documentation (as WhatsApp READMEs), those files land in this `~R&D/` directory. Each README becomes a structured integration assessment + URAP component spec before any code is written.

---

## Payload Contract (URAP ↔ BizReach Pro)

Both systems use this shared lead payload schema:

```json
{
  "first_name": "string",
  "last_name": "string",
  "business_name": "string",
  "email": "string",
  "phone": "string",
  "address": "string",
  "city": "string",
  "state": "string",
  "zip": "string",
  "category": "string",
  "score": "integer (0–100)",
  "source": "string",
  "timestamp": "ISO 8601"
}
```

URAP's `LeadRouterService` payload is a superset. When dispatching to BizReach marketplaces, strip to this schema. When receiving from BizReach, map to `InboundLead` and enrich via `EnrichmentService`.

---

## Current UI Pages

| Route | Page | Module |
|---|---|---|
| `/prospector` | Prospector | m1 + m2 |
| `/companies` | Company Search | m1 |
| `/emailing` | Email Sequences | m2 |
| `/buyer-intent` | Buyer Intent Signals | m1 |
| `/job-changes` | Job Change Alerts | m1 |
| `/connect` | LinkedIn Connect | m2 |
| `/warp-mode` | Warp Mode AI Copilot | m3 |
| `/autopilot` | Autopilot Scheduler | m5 |
| `/reply-intel` | Reply Intelligence | m3 |
| `/calling` | Voice Calling | m2 |
| `/integrations` | Integrations & Webhooks | m5 |
| `/api-keys` | API Key Manager | m5 |
| `/bulk-credits` | Bulk Enrichment | m1 |

---

## Integration Roadmap

### Phase 1 — Route Core
> Adds lead routing to external buyer marketplaces in the URAP UI.

**New page: `/lead-router`** (`LeadRouter.tsx`)
- Lead queue: filters (Min Score, Has Email, Hide Routed, Category)
- Marketplace selector from configured webhook targets
- Route Selected + Ping/Post toggle
- TCPA compliance gate (fires `ConsentLedgerService` before any dispatch)
- Session log: platform, lead count, estimated earnings per run

**Extend `/integrations`** — add Marketplaces section
- 18 pre-loaded marketplace cards (PX, LeadsMarket, LeadPoint, LeadExec, Modernize, etc.)
- Per-card: Webhook URL, API Key, CPL target, Test Webhook
- Auto-save to Supabase

**New backend: `m4_inbound/marketplace_router.py`**
- `dispatch_to_marketplace(lead, webhook_url, api_key)` → POST JSON payload
- `test_webhook(webhook_url)` → sample payload validation → 200 OK check
- `mark_lead_routed(lead_id, platform, cpl)` → logs routing session to `urap_routing_sessions`
- `get_routing_history(tenant_id, limit)` → session log for UI

**Extend `/autopilot`**
- Add marketplace target selector + score threshold for route jobs
- AutopilotRunner job types: `warp_mode` (existing) + `route_to_marketplace` (new)

**New Supabase table: `urap_routing_sessions`**
```sql
id, tenant_id, platform_name, lead_count, estimated_earnings, status, created_at
```

---

### Phase 2 — Monetization Layer
> Revenue visibility, max CPL via Race Agents, income method playbook.

**New page: `/revenue`** (`Revenue.tsx`)
- 9 income method cards: PPL Insurance, PPL Solar/Home, PPL Legal, Directory Sites, BizReach Affiliate, GHL Affiliate, CRM SaaS Affiliates, AI Tool Affiliates, DFY Agency
- Filter: All / Pay Per Lead / Directory / SaaS Affiliates / Agency
- Each card: monthly potential range, difficulty badge, time-to-first-dollar, expandable step-by-step, direct program links
- Deploy NaviTeam section per method → triggers WarpMode agents with ICP context
- Revenue Stack calculator: select active methods → combined monthly projection
- Full Stack panel: stacked total with 12-agent NaviTeam deploy buttons

**New backend: `m4_inbound/race_agents.py`**
- `run_cpl_auction(lead, configured_marketplaces)` → fires ping to all platforms in parallel
- Collects responses + CPL bids, returns winner
- Wraps `marketplace_router.dispatch_to_marketplace` — auction mode is ping-post with competitive selection
- Logs auction results + CPL delta vs flat routing

**Dashboard widgets on `/lead-router`**
- Pipeline Funnel: Found → Enriched → Qualified → Routed → Earned
- Earnings Chart: 30-day routing revenue bar chart
- Revenue Goal: monthly target input → leads/day + recommended interval output
- Break-even calculator

**Extend `/reply-intel`** — Buyer Inbox section
- Filter tabs: All / Hot / Replied / New Inquiry / Prospect
- Status badges: 🔥 Hot, 💛 Replied, 🔵 Buyer Inquiry, 🟣 Prospect
- Maps to `ReplyIntelligenceAgent` intent classification (already has meeting_set, interested, unsubscribed signals)

---

### Phase 3 — Kenny's API Bridge
> Bidirectional lead + config sync between URAP and BizReach Pro.

**URAP as BizReach lead enrichment provider:**
- BizReach's ElecMan.EXE posts leads to a URAP tenant webhook
- URAP enriches via waterfall (Hunter + Cleanlist + Apollo)
- URAP fires enriched lead back to BizReach at higher CPL

**Marketplace config sync API:**
- `GET /api/marketplaces/export` → URAP tenant exports their webhook configs as JSON
- BizReach Pro imports via its marketplace config UI
- One source of truth for webhook URLs shared across both platforms

**Agent relay handshake:**
- BizReach Relay Pipeline Step 11 (Webhook Routing) can call URAP's `/api/route/dispatch` endpoint
- URAP's AutopilotRunner can call BizReach's Relay Pipeline trigger endpoint
- Both apps emit completion events that the other can listen on

---

## R&D Intake Process

When new BizReach Pro tab documentation arrives (via WhatsApp or direct share):

1. **Drop README into `~R&D/`** — raw file, no edits
2. **CIO requests assessment** — tag the files, ask for integration plan
3. **Agent reads this directive + GRAPH_REPORT.md** — maps new tab to URAP god nodes and communities
4. **Agent writes assessment** — structural mapping table, 3-phase plan, new pages + backend specs
5. **CIO approves scope** — phase selection, sprint assignment
6. **Agent writes spec file** — `~R&D/SPEC_[TAB_NAME]_[DATE].md` with component contracts
7. **Implementation begins** — new pages registered in `registry.ts`, new backend in appropriate module
8. **Update this directive** — add new pages to the UI table, update roadmap status

**Architecture rules for R&D intake:**
- Never create a standalone page that duplicates a god node's logic — always extend the god node
- New pages register via `registerTool()` in `registry.ts` — no hardcoded nav
- TCPA gate is mandatory for any feature that dispatches outreach or routes leads
- Backend additions go in the correct module (m1–m6) — no new top-level modules without CIO approval
- All new Supabase tables are named `urap_[noun]_[noun]` (snake case, no generic "data" or "records")

---

## Version History

| Date | Author | Change |
|---|---|---|
| 2026-06-02 | CIO / Claude (IT) | Initial directive created from BizReach Route Tab + Money Tab R&D intake |
