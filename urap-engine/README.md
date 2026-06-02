# urap-engine

Python FastAPI microservice powering the URAP platform. All business logic — enrichment, outreach, AI agents, compliance, billing — lives here. The frontend (`urap-app`) and the middleware plugin (`urap-core`) both talk to this service over HTTP.

---

## Tech Stack

| Layer | Choice |
|---|---|
| Framework | FastAPI 0.115 + Uvicorn |
| Language | Python 3.12 (required — see below) |
| Data | Supabase (Postgres + RLS) |
| HTTP client | httpx (async) |
| AI agents | Google ADK + OpenRouter pattern |
| Email | SMTP2GO → Brevo → Mailgun waterfall |
| Voice/SMS | Twilio |
| Billing | Stripe metered |
| Auth | `x-api-key` header + `x-tenant-id` header |

### Python Version Constraint

**Python 3.12 is required.** `pydantic 2.8` is incompatible with Python 3.14. The `start.sh` script creates and manages a dedicated venv at `/tmp/urap-venv` using the system Python 3.12 binary. Do not use the system Python directly.

---

## Getting Started

```bash
cd urap-engine
cp .env.example .env    # fill in required variables
./start.sh              # bootstraps venv on first run, then starts uvicorn
```

The engine starts on `http://localhost:8080` with `--reload` enabled for hot-reloading on file saves.

Health check:

```bash
curl http://localhost:8080/health
# → {"status":"ok","service":"urap-engine","version":"0.1.0"}
```

### Authentication in Development

Leave `URAP_API_KEY` blank in `.env` to run in open dev mode (no key required). Set it to any string to enable key enforcement. All dashboard requests must then include:

```
x-api-key: <your-key>
x-tenant-id: <tenant-id>
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in values. Never commit `.env`.

```env
# ── Required ─────────────────────────────────────────────────────────────────
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key

# ── Auth (leave blank = open dev mode) ────────────────────────────────────────
URAP_API_KEY=
URAP_ALLOWED_ORIGINS=*        # comma-separated for production

# ── Enrichment waterfall ──────────────────────────────────────────────────────
# Hunter.io — 50 free domain-search requests/month. https://hunter.io
HUNTER_API_KEY=

# Yelp Fusion — local business search + details. https://www.yelp.com/developers
YELP_API_KEY=

# Prospeo — 75 verified emails/month free, no CC. https://prospeo.io
PROSPEO_API_KEY=

# Snov.io — 50 credits/month free. https://snov.io
SNOV_CLIENT_ID=
SNOV_CLIENT_SECRET=

# Cleanlist.ai — 30 credits/month free. https://cleanlist.ai
CLEANLIST_API_KEY=

# ── Email sending (own-domain SMTP) ──────────────────────────────────────────
SMTP2GO_API_KEY=      # primary — 1,000 emails/month free
BREVO_API_KEY=        # overflow — 300/day free
MAILGUN_API_KEY=      # burst fallback — 3,000/month free
MAILGUN_DOMAIN=

# ── Voice / SMS ───────────────────────────────────────────────────────────────
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=
```

---

## Module Structure

```
server/
  main.py              FastAPI app, all route definitions
  middleware.py        API key auth dependency

modules/
  m1_intelligence/     Module I — Data Enrichment
    company_search.py  Multi-source company search (Google Places, Yelp, Foursquare)
    contact_discover.py Contact discovery waterfall + social profile scraping
    enrichment.py      Prospeo/Snov.io/Hunter enrichment service
    lead_lists.py      Saved lead list CRUD (Supabase)

  m2_outreach/         Module II — Outreach Engine
    channel_state_machine.py  Per-lead channel states; pauses all on reply
    email_sequence.py         Single email send + intent scoring
    drip_sequences.py         3-step drip templates + enrollment + hourly tick

  m3_agents/           Module III — AI Sales Agents
    warp_mode.py       ICP → search → AI copy (Gemini Flash) → review (Claude) → queue
    reply_intelligence.py  Parse reply → classify → update status → calendar + Telegram

  m4_inbound/          Module IV — Inbound Lead Capture
    lead_router.py     Capture → ping-post preview/claim → geo-routing

  m5_api/              Module V — API Infrastructure
    api_key_manager.py  Tenant API key generation + revocation (hashed storage)
    bulk_enrich_runner.py  CSV and ICP bulk enrichment jobs
    autopilot_runner.py   Scheduled ICP → enrich → enroll automation

  m6_compliance/       Module VI — Security & Compliance
    consent_ledger.py  TrustedForm cert storage, TCPA gate check

tier3/                 Third-party API client wrappers
  brevo/               Overflow SMTP sender
  cleanlist/           Email verification + quality gate
  gcalendar/           Google Calendar event creation (meeting_set trigger)
  hunter/              Domain-search email enrichment
  mailgun/             Burst fallback SMTP
  prospeo/             Primary contact enrichment
  smtp2go/             Primary SMTP sender
  snov/                Enrichment fallback
  telegram/            AE alert on qualified lead
  twilio/              Power dialer + SMS
  zapier/              Webhook subscription + dispatch
```

---

## API Reference

All endpoints require `x-tenant-id` header. Endpoints marked **[auth]** also require `x-api-key`.

### Health

```
GET /health
→ { status, service, version }
```

### Module I — Company Search & Contact Discovery

#### Search Companies
```
POST /companies/search  [auth]
Body: { domain?, name?, keywords?, location?, industry?, limit? }
→ { companies: CompanyResult[], count }
```

**Search modes:**
- `domain` provided → enrichment lookup (Hunter/Snov.io) for a single known company
- `keywords` + `location` + `industry` → multi-source local discovery (Google Places, Yelp, Foursquare)

Each `CompanyResult` includes: `name`, `domain`, `website`, `yelp_id`, `phone`, `location`, `industry`, `source`, `rating`, `reviews`.

#### Discover Contact for One Company
```
POST /companies/contact  [auth]
Body: { name?, domain?, website?, phone?, yelp_id? }
→ { email, first_name, last_name, title, confidence, source, phone,
    linkedin, instagram, twitter, youtube }
```

**Discovery waterfall:**
1. If `yelp_id` provided and no domain → calls Yelp details API for real website
2. If still no domain → guesses `<slug>.com` patterns from business name with HEAD verification
3. Hunter.io domain-search **and** social profile scraping run in **parallel**
4. Falls back to scraping the website for `mailto:` emails
5. Social profiles (LinkedIn company page, Instagram, Twitter/X, YouTube) are always returned if found

#### Discover Contacts in Batch
```
POST /companies/contact/batch  [auth]
Body: { companies: [{ index, name, domain, website, phone, yelp_id }], max_parallel? }
→ { results: [{ index, email, first_name, last_name, title, confidence, source, phone,
                linkedin, instagram, twitter, youtube }], count }
```

Runs with a semaphore (default 5 concurrent). Max 10.

#### Lead Lists
```
POST   /companies/list/save       [auth]  Save search results as a named list
GET    /companies/lists           [auth]  List all saved lists
GET    /companies/list/{list_id}  [auth]  Get items in a saved list
DELETE /companies/list/{list_id}  [auth]  Delete a list
```

### Module II — Outreach Engine

#### Send Single Email
```
POST /outreach/email/send  [auth]
Body: { lead_id, to_email, to_name, from_email, from_name, subject, body_html, require_consent? }
→ { success, provider, message_id, error }
```

Tries SMTP2GO → Brevo → Mailgun in order until one succeeds.

#### Drip Sequences
```
POST /outreach/sequence/create  [auth]  Create a 3-step sequence template
GET  /outreach/sequences        [auth]  List templates for tenant
POST /outreach/sequence/enroll  [auth]  Enroll a contact; Step 0 fires within 1 hour
POST /outreach/sequence/tick    [auth]  Manually trigger the hourly step runner
```

The tick runner also fires automatically every hour in the background.

#### Channel State Events
```
POST /outreach/channel/event  [auth]
Body: { lead_id, channel, event }
  channel: email | sms | linkedin | voice
  event:   reply | send | open | bounce | unsubscribe | meeting_set
```

A `reply` event pauses all other channels for that lead. `meeting_set` fires Google Calendar and Telegram. Any globalStatus change dispatches registered Zapier webhooks.

#### Intent Scoring
```
POST /outreach/intent/score  [auth]
Body: { domain?, limit? }
→ { contacts: [{ score, ...contactFields }], count }
```

### Module III — AI Agents

#### Warp Mode
```
POST /agents/warp/run  [auth]
Body: { domain, title?, industry?, value_prop?, icp_label?, limit? }
→ { job_id, icp_label, leads_found, sequences_queued, generated, error }
```

Finds companies matching the ICP, enriches contacts, generates personalized outreach copy (Gemini Flash → Claude Sonnet review), and queues them to drip sequences.

```
GET /agents/warp/jobs  [auth]   List recent Warp Mode jobs
```

#### Reply Intelligence
```
POST /agents/reply/parse  [auth]
Body: { lead_id, channel, reply_text }
→ { lead_id, channel, sentiment, confidence, global_status_updated_to,
    calendar_link, telegram_sent, summary }
```

Classifies reply sentiment, updates `globalStatus`, creates a Google Calendar event on `meeting_set`, and fires a Telegram alert on `qualified`.

### Module IV — Inbound Lead Capture

```
POST /leads/capture                   (public)  Capture inbound lead, return preview
GET  /leads/preview/{preview_id}  [auth]         Get anonymized preview attributes
POST /leads/claim                 [auth]         Claim full PII; fires Stripe metered event
GET  /leads/recent                [auth]         List recent captured leads
```

### Module V — API & Billing

#### Developer API Keys
```
POST   /api/keys          [auth]  Generate a new key (plaintext returned once)
GET    /api/keys          [auth]  List keys (prefix + metadata only)
DELETE /api/keys/{key_id} [auth]  Revoke a key
```

#### Zapier Integrations
```
POST   /integrations/zapier/subscribe        [auth]  Register webhook for a globalStatus event
DELETE /integrations/zapier/{webhook_id}     [auth]  Remove a webhook
GET    /integrations/zapier                  [auth]  List all subscriptions
```

#### Bulk Enrichment
```
POST /enrich/bulk-job/csv  [auth]  Run enrichment from CSV text
POST /enrich/bulk-job/icp  [auth]  Run enrichment for all contacts at a domain
GET  /enrich/bulk-job/{id} [auth]  Get job status
GET  /enrich/bulk-jobs     [auth]  List recent jobs
```

#### Autopilot
```
POST /autopilot/enable   [auth]  Enable and configure scheduled ICP run
POST /autopilot/disable  [auth]  Disable Autopilot
GET  /autopilot/config   [auth]  Get current config
POST /autopilot/run      [auth]  Trigger one Autopilot cycle manually
```

#### One-Shot ICP Runner
```
POST /outreach/autopilot/run-icp  [auth]
Body: { keywords, location, industry, limit, sequence_id }
→ { companies_found, emails_discovered, enrolled, sequence_id }
```

Searches companies, enriches contacts, and enrolls all found emails into a sequence in one request.

### Module VI — TCPA Consent

```
POST /consent/record  (public)  Record a TrustedForm consent certificate
POST /consent/check   [auth]    TCPA gate — returns consented: true/false
```

**Always call `/consent/check` before queuing SMS or voice outreach.** The ledger is insert-only.

### Voice & SMS

```
POST /voice/dial              [auth]  Initiate outbound call
GET  /voice/status/{call_sid} [auth]  Get call status
POST /voice/hangup/{call_sid} [auth]  End active call
POST /sms/send                [auth]  Send SMS (TCPA gate enforced internally)
```

### Webhooks

```
POST /webhooks/brevo          Brevo delivery/open/click/bounce/unsub events
POST /webhook/{module}        Generic webhook receiver
```

---

## Company Search: How Sources Work

The `/companies/search` endpoint fans out to three free-tier APIs simultaneously:

| Source | API | Best For |
|---|---|---|
| Google Places | `googlemaps` (Places Text Search) | Any business type, global coverage, website URLs |
| Yelp Fusion | Yelp Fusion v3 | US local businesses, ratings, reviews, phone numbers |
| Foursquare | Foursquare Places v3 | Urban venues, additional coverage |

Results are deduplicated by name. A post-filter enforces the requested location by matching city/state tokens against the `location` field when Yelp's free tier ignores the `location` param.

---

## Contact Discovery: The Waterfall

For each company, discovery runs in this order:

1. **Yelp details API** (if `yelp_id` present) → fetches real business website
2. **Domain guessing** (fallback) → tries `<fullname>.com`, `<stripped>.com`, `<firsttwo>.com`, `<first>.com` patterns with HEAD verification (min 6-char slug to avoid generic hits like `law.com`)
3. **Hunter.io domain-search** and **social profile scraping** run **in parallel**
4. **Website email scrape** → checks homepage, `/contact`, `/contact-us` for `mailto:` addresses

Social scraping targets: LinkedIn company pages, Instagram, Twitter/X (with path exclusions for non-profile URLs), YouTube channels and `@handles`.

---

## Supabase Tables

| Table | Purpose |
|---|---|
| `urap_contacts` | Enriched contact cache, per-tenant |
| `urap_consent_ledger` | TrustedForm cert records (insert-only via RLS) |
| `urap_lead_distribution` | Captured inbound leads + ping-post state |
| `urap_sequences` | Drip sequence templates |
| `urap_enrollments` | Per-contact sequence enrollment state |
| `urap_zapier_webhooks` | Registered Zapier webhook URLs |
| `urap_api_keys` | Hashed developer API keys |
| `urap_lead_lists` | Saved search result list metadata |
| `urap_lead_list_items` | Items within each saved list |
| `urap_bulk_jobs` | Bulk enrichment job records |
| `urap_autopilot_config` | Per-tenant Autopilot ICP + schedule |
| `urap_warp_jobs` | Warp Mode job records |

---

## Deployment

The engine is designed to deploy on **Google Cloud Run** alongside `dabblin-voice`:

```bash
# Build
docker build -t urap-engine .

# Run locally
docker run -p 8080:8080 --env-file .env urap-engine

# Deploy to Cloud Run
gcloud run deploy urap-engine \
  --image gcr.io/YOUR_PROJECT/urap-engine \
  --platform managed \
  --region us-east1 \
  --set-env-vars SUPABASE_URL=...,SUPABASE_ANON_KEY=...
```

`.env` is listed in `.dockerignore`. Pass secrets via Cloud Run env vars or Secret Manager — never bake them into the image.

---

## Adding a New Tier-3 Integration

1. Create `tier3/<provider>/client.py` with async functions
2. Add provider API key to `.env.example` and `.env`
3. Import and call from the relevant module (e.g., add to the enrichment waterfall in `m1_intelligence/enrichment.py`)
4. No changes to `server/main.py` needed unless a new endpoint is required
