# URAP — Unified Revenue Acceleration Platform

**Unified Revenue Acceleration Platform** is an AI-agent-driven outbound revenue stack built by [Antigravity / Dabblin Cloud Technologies](https://dabblin.com). It consolidates prospecting, contact enrichment, omni-channel outreach, and AI automation into one product instead of stitching together Apollo, Kular, Instantly, and ClickPoint.

---

## Repository Layout

```
urap/
├── urap-app/        React + Vite frontend dashboard (port 3034)
├── urap-engine/     Python FastAPI microservice — all AI agent logic (port 8080)
└── urap-core/       @antigravity/urap-core — Express middleware npm package
```

Each package has its own README with full setup and API details. Start there when working on a specific component.

---

## Architecture Overview

URAP is a **two-component plugin system**:

```
┌─────────────────────────────────────────────────────────────┐
│                    HOST APPLICATION                          │
│  app.use('/urap', urapMiddleware({ apiKey, tenantId }))      │
│              ↕  @antigravity/urap-core                       │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP proxy
┌──────────────────────▼──────────────────────────────────────┐
│               urap-engine  (Python / FastAPI)                │
│  Port 8080 · Docker/Cloud Run · All LLM + enrichment logic   │
└─────────────────────────────────────────────────────────────┘
```

| Component | Role |
|---|---|
| `urap-engine` | Python FastAPI microservice. All business logic lives here: enrichment waterfall, outreach sequences, AI agents (Warp Mode, Reply Intelligence), consent ledger, Zapier webhooks, Stripe billing. |
| `urap-core` | Thin Express middleware. Host sites `npm install` and mount it. Proxies every call through to the engine. Also serves the embeddable inbound lead capture form (`/urap/embed.js`). |
| `urap-app` | Standalone React dashboard. The primary UI for SDRs and admins. Talks directly to the engine over HTTP. Not required for hosts using only the middleware plugin. |

### Multi-Tenant Design

Every engine request is scoped by `x-tenant-id` header + `x-api-key` header. One engine instance serves any number of client tenants. Tenant data is isolated in Supabase via row-level security.

---

## The Six Modules

| # | Module | What It Does |
|---|---|---|
| I | **Global Intelligence & Data Enrichment** | Company search (Google Places, Yelp, Foursquare), contact discovery waterfall (Hunter → website scrape), social profile scraping |
| II | **Omni-Channel Outreach Engine** | 3-step drip sequences via SMTP2GO → Brevo → Mailgun waterfall; channel state machine pauses all channels on reply |
| III | **AI Sales Agents** | Warp Mode (ICP → enrich → AI copy → queue), Reply Intelligence (sentiment parse → calendar event → Telegram alert) |
| IV | **Inbound Lead Capture & Distribution** | Ping-post preview/claim system, TrustedForm consent, geo-routing |
| V | **API & Billing** | Tenant-scoped REST API, developer API keys, Stripe metered billing per qualified lead, Zapier webhooks |
| VI | **Security & Compliance** | TCPA consent ledger (insert-only), PCI SAQ A, GDPR LIA documentation |

---

## Core Data Model — LeadStatusObject

The single shared state object that flows through every module:

```typescript
interface LeadStatusObject {
  leadId:      string;
  tenantId:    string;
  contactData: { name, email, phone, company, title, intentSignals[] };
  channelState: {
    email:    'idle' | 'sent' | 'opened' | 'replied' | 'bounced' | 'paused';
    sms:      'idle' | 'sent' | 'replied' | 'opted_out' | 'paused';
    linkedin: 'idle' | 'connected' | 'messaged' | 'replied' | 'paused';
    voice:    'idle' | 'dialed' | 'answered' | 'voicemail' | 'paused';
  };
  globalStatus: 'prospecting' | 'engaged' | 'interested' | 'meeting_set'
              | 'qualified' | 'not_interested' | 'unsubscribe';
  consentRecord?: { source, consentedAt, ipAddress, oneToOneRule, platformName };
}
```

**Key rule:** A reply on any channel sets `globalStatus` and pauses all other channel tasks immediately. The channel state machine in `m2_outreach/channel_state_machine.py` enforces this.

---

## Quick Start (Local Development)

### Prerequisites

- Node.js 18+
- Python 3.12 (required — see engine README)
- Supabase project (free tier works)

### 1. Start the Engine

```bash
cd urap-engine
cp .env.example .env   # fill in at minimum SUPABASE_URL + SUPABASE_ANON_KEY
./start.sh             # creates /tmp/urap-venv automatically on first run
```

Engine is live at `http://localhost:8080`. Health check: `GET /health`.

### 2. Start the Dashboard

```bash
cd urap-app
cp .env.example .env   # set VITE_ENGINE_URL if not localhost:8080
npm install
npm run dev            # http://localhost:3034
```

### 3. (Optional) Mount the Middleware Plugin

```bash
cd urap-core
npm install
npm run build
```

In your Express app:

```typescript
import { urapMiddleware } from '@antigravity/urap-core';

app.use('/urap', urapMiddleware({
  apiKey:    process.env.URAP_API_KEY,
  tenantId:  'your-client-id',
  engineUrl: 'https://your-engine.run.app',   // default: http://localhost:8080
}));
```

---

## Environment Variables Summary

| Variable | Component | Required | Description |
|---|---|---|---|
| `SUPABASE_URL` | engine | Yes | Supabase project URL |
| `SUPABASE_ANON_KEY` | engine | Yes | Supabase anon key |
| `URAP_API_KEY` | engine | Dev: no | Shared API key — leave blank for open dev mode |
| `HUNTER_API_KEY` | engine | Recommended | Hunter.io — 50 free domain-search credits/month |
| `YELP_API_KEY` | engine | Recommended | Yelp Fusion — local business search |
| `PROSPEO_API_KEY` | engine | Optional | Prospeo — 75 verified emails/month free |
| `SMTP2GO_API_KEY` | engine | Sprint 3+ | Primary email sender |
| `BREVO_API_KEY` | engine | Sprint 3+ | Overflow email sender |
| `TWILIO_*` | engine | Sprint 5+ | Voice/SMS |
| `VITE_ENGINE_URL` | app | Dev: no | Engine URL for the dashboard (default: `http://localhost:8080`) |
| `VITE_TENANT_ID` | app | Dev: no | Tenant for dashboard requests (default: `local`) |

Full variable list with sign-up links: `urap-engine/.env.example`.

---

## Sprint Roadmap

| Sprint | Deliverables |
|---|---|
| 0 | Foundation: Supabase schema, repo scaffold, first STM memos |
| 1 | **Prospector**, **Companies Search** — enrichment waterfall, UI |
| 2 | TCPA consent ledger, TrustedForm integration, FastAPI scaffold |
| 3 | **Buyer Intent**, **Job Changes**, **Connect**, **Emailing** — drip sequences, channel state machine |
| 4 | **Warp Mode**, **Autopilot**, **Reply Intelligence** — AI agents, calendar trigger, Telegram alerts |
| 5 | **Calling** — Twilio Power Dialer, ping-post, inbound lead capture |
| 6 | **Integrations**, **API**, **Bulk Enrich** — Zapier webhooks, developer API, Stripe billing |
| 7 | `@antigravity/urap-core` npm package, Docker/Cloud Run deploy, E2E test |
| 8 | CCPA/GDPR/TCPA docs, EU-US DPF, OpenAPI published, GTM sales deck |
| 9 (post-MVP) | **Social Selling** — LinkedIn outreach via Apify |

---

## Security Notes

- `.env` is in `.dockerignore` and `.gitignore` — **never commit it, never bake into a Docker image**
- TCPA gate (`/consent/check`) must be called before any SMS or voice outreach
- TrustedForm cert URLs are stored insert-only in `urap_consent_ledger` — no updates or deletes
- API keys are stored hashed in Supabase; plaintext is returned only once at creation

---

## Team & Ownership

| Role | Owner | Scope |
|---|---|---|
| Product / Sales | DAB AGENT Sales (Saiyan Prime) | Modules I–III, pricing model |
| Engineering | DAB AGENT CIO (Majin Vegeta) | Engine, frontend, infrastructure |
| Compliance / Legal | DAB AGENT CLO (Master Roshi) | Module VI, TCPA, GDPR |
| Finance | DAB AGENT CFO | Stripe billing reconciliation |
| GTM | DAB AGENT CBO (Sailor Uranus) | Zapier Marketplace, sales deck |

STM memos are written to `agents/departments/[Dept]/URAP/02_project_memos.log` at the close of every sprint per the Gravity-Claw STM Protocol.
