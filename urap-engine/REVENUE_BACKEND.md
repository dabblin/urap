# Revenue Page — Backend Reference

The `/revenue` page in `urap-app` is the income-method catalog and CPL auction control center. It calls two backend endpoints on startup and two more when the user fires a CPL Race. This document covers every backend component that powers the page.

---

## Page → Backend Call Map

| Trigger | Method | Endpoint | Handler |
|---|---|---|---|
| Page load | `GET` | `/race/results` | `race_results()` |
| "Run CPL Race" button | `POST` | `/outreach/intent/score` | `score_intent()` |
| "Run CPL Race" button (step 2) | `POST` | `/race/run` | `race_run()` |
| After race completes | `GET` | `/race/results` | `race_results()` (re-fetched) |

All four require `x-api-key` and `x-tenant-id` request headers.

---

## Endpoint Reference

### GET `/race/results`

Returns the CPL auction history and aggregate stats for the sidebar's **CPL Auction Stats** card and the **Recent CPL Auctions** table.

**Response:**
```json
{
  "results": [
    {
      "auction_id": "uuid",
      "lead_id": "uuid-or-email",
      "winner_marketplace_id": "px",
      "winner_marketplace_name": "PX Marketplace",
      "winning_cpl": 87.50,
      "all_bids": [
        { "marketplace_id": "px", "marketplace_name": "PX Marketplace", "cpl": 87.50, "accepted": true, "error": "" },
        { "marketplace_id": "leadsmarket", "marketplace_name": "LeadsMarket", "cpl": 62.00, "accepted": true, "error": "" }
      ],
      "dispatched": true,
      "error": "",
      "created_at": "2026-06-02T14:00:00Z"
    }
  ],
  "total_auctions": 12,
  "auctions_won": 9,
  "total_earned": 731.25
}
```

**Source:** `modules/m4_inbound/race_agents.py` → `RaceAuction.get_results()`

Reads from Supabase table `urap_race_results`, ordered by `created_at` desc, limit 20.

---

### POST `/outreach/intent/score`

Called first when a CPL Race fires. Retrieves contacts from the tenant's enrichment cache, scores each by intent signal, and returns the top results sorted by score descending.

**Request:**
```json
{ "limit": 10 }
```

**Response:**
```json
{
  "contacts": [
    { "score": 82, "id": "uuid", "email": "owner@hvac.co", "first_name": "Marcus", "company": "Atlanta HVAC", ... },
    ...
  ],
  "count": 10
}
```

**Scoring:** Enrichment-signal scoring via `EmailSequenceService.score_intent()`. Full 3rd-party intent signals (BuyerSense, G2, Bombora) are planned for Sprint 4.

**Source:** `server/main.py` → `score_intent()`, reads `urap_contacts` table.

---

### POST `/race/run`

Runs the CPL auction. The frontend passes the top 5 scored contacts as `leads`.

**Request:**
```json
{
  "leads": [ { "id": "uuid", "email": "...", "first_name": "...", ... } ],
  "timeout": 5.0
}
```

**Response:**
```json
{
  "results": [
    {
      "auction_id": "uuid",
      "lead_id": "uuid",
      "winner_marketplace_id": "px",
      "winner_marketplace_name": "PX Marketplace",
      "winning_cpl": 115.00,
      "all_bids": [...],
      "dispatched": true,
      "error": "",
      "created_at": "2026-06-02T15:30:00Z"
    }
  ],
  "total_auctions": 5,
  "auctions_won": 4,
  "total_earned": 392.50
}
```

**Source:** `server/main.py` → `race_run()` → `modules/m4_inbound/race_agents.py` → `RaceAuction.run_bulk()`

---

## CPL Auction Engine (`race_agents.py`)

**Class:** `RaceAuction`

### How a single auction works (`run_auction`)

1. **Load configs** — queries `urap_marketplace_configs` for all rows where `tenant_id` matches and `webhook_url` is not blank.
2. **Simultaneous ping** — fires `asyncio.gather()` to all configured marketplace webhooks in parallel. Each ping POST includes the lead payload plus `"ping": true` to signal an auction inquiry rather than a final lead post.
3. **Parse bids** — if the marketplace returns `{"cpl": N, "accepted": true}` in the response body, that CPL is used. If the body cannot be parsed, the static CPL value saved in `urap_marketplace_configs` is used as fallback.
4. **Pick winner** — sorts accepting bids by CPL descending; highest CPL wins.
5. **Dispatch** — POSTs the full lead payload (without `ping: true`) to the winner's webhook URL. Bearer token from config is attached if set.
6. **Mark lead** — updates `routed_at` on the contact row in `urap_contacts`.
7. **Log result** — inserts a row into `urap_race_results`.

### Bulk mode (`run_bulk`)

Runs auctions sequentially per lead (not parallel) to avoid hammering marketplaces simultaneously. The frontend sends at most 5 leads per race.

### Lead payload schema sent to marketplaces

```json
{
  "first_name": "Marcus",
  "last_name": "Wright",
  "business_name": "Atlanta HVAC",
  "email": "owner@hvac.co",
  "phone": "404-555-0100",
  "address": "",
  "city": "Atlanta",
  "state": "GA",
  "zip": "",
  "category": "HVAC",
  "score": 82,
  "source": "urap_race",
  "timestamp": "2026-06-02T15:30:00Z"
}
```

---

## Marketplace Router (`marketplace_router.py`)

**Class:** `MarketplaceRouter`

Manages the 18-marketplace catalog and per-tenant webhook configurations. Used directly by the Lead Router tab but also read by `RaceAuction._get_configs()`.

### Marketplace Catalog

18 pre-loaded buyer marketplaces are hardcoded in `MARKETPLACE_CATALOG`. Each entry has:

| Field | Description |
|---|---|
| `id` | Slug used as `marketplace_id` in Supabase |
| `name` | Display name |
| `cpl_range` | Typical CPL range (informational) |
| `best_for` | Use case description |

Catalog entries include: PX Marketplace, LeadsMarket, LeadPoint, LeadExec/ClickPoint, LeadCrowd, Referr, LeadNinja, Oversource, Elite Lead Exchange, SaleSpread, Leadfellow, LeadSwap, CloudTask Marketplace, E-Prospects.biz, GoTradeLeads, Serchz, Premier Business Club, and Custom/Agency.

### Tenant Config (webhook setup)

Each tenant configures webhooks per marketplace via the Lead Router tab. Stored in `urap_marketplace_configs`:

| Column | Type | Description |
|---|---|---|
| `id` | UUID | Row PK |
| `tenant_id` | text | Tenant scope |
| `marketplace_id` | text | Matches catalog `id` |
| `webhook_url` | text | Buyer's receiving endpoint |
| `api_key` | text | Optional Bearer token |
| `cpl` | float | Static CPL fallback if dynamic bid fails |
| `created_at` / `updated_at` | timestamptz | Audit timestamps |

Only marketplaces with a non-empty `webhook_url` participate in CPL races.

---

## Supabase Tables Used by the Revenue Page

| Table | Purpose |
|---|---|
| `urap_race_results` | Auction log — one row per lead per race. Queried by `/race/results`. |
| `urap_marketplace_configs` | Per-tenant webhook + CPL config. Read by `RaceAuction` and `MarketplaceRouter`. |
| `urap_contacts` | Enriched contact cache. Read by `/outreach/intent/score` to source auction candidates. |

---

## Data Flow Diagram

```
Revenue page loads
       │
       ▼
GET /race/results ──────────────────► urap_race_results (Supabase)
       │                                      │
       │                               Returns stats + history
       │                                      │
       ▼                                      ▼
CPL Auction Stats card              Recent Auctions table
       │
"Run CPL Race" clicked
       │
       ▼
POST /outreach/intent/score ─────────► urap_contacts (Supabase)
       │                                      │
       │                             Scored contacts returned
       │                             (top 5 sent to auction)
       ▼
POST /race/run
       │
       ├─── asyncio.gather() ──► Marketplace 1 webhook (ping)
       │                    ──► Marketplace 2 webhook (ping)
       │                    ──► Marketplace N webhook (ping)
       │
       │    All bids collected; highest CPL wins
       │
       ├─── POST to winner webhook (full lead payload)
       │
       ├─── urap_contacts.routed_at updated
       │
       └─── urap_race_results INSERT
                    │
                    ▼
       GET /race/results (re-fetched to update UI)
```

---

## Income Method Catalog (Static)

The 9 income methods displayed on the page — Pay Per Lead (Insurance, Solar, Legal), Directory Sites, SaaS Affiliates (BizReach, GHL, CRM stack, AI tools), and Agency Model — are **hardcoded in the frontend** at `urap-app/src/pages/Revenue.tsx` in the `METHODS` array. There is no backend endpoint for these; they are static content.

The `canRace: true` flag on PPL methods (`ppl-insurance`, `ppl-solar`, `ppl-legal`) is what enables the "Run CPL Race" button for those cards.

---

## Configuration Prerequisites

A CPL race will return `"No configured marketplaces for this tenant"` unless at least one marketplace webhook is saved for the tenant. To configure:

1. Go to **Lead Router** tab in the URAP dashboard
2. Select a marketplace from the 18-entry catalog
3. Paste the buyer's webhook URL
4. Set a static CPL fallback (used if the marketplace doesn't return a dynamic bid)
5. Optionally add a Bearer API key

This calls `POST /route/marketplace/{marketplace_id}` and saves to `urap_marketplace_configs`.

To verify a webhook before racing, use `POST /route/test-webhook` — sends a synthetic sample lead and checks for a 2xx response.

---

## Error States

| Condition | UI behavior | Root cause |
|---|---|---|
| No scored leads | `alert()` shown | `urap_contacts` is empty — run Warp Mode or add contacts first |
| No configured marketplaces | Auction runs, `dispatched: false`, `error: "No configured..."` | No webhook saved for tenant |
| All bids timeout | `dispatched: false`, `error: "No marketplace accepted..."` | Marketplace webhooks not responding within 5s |
| Bid HTTP error | That marketplace's `accepted: false` | Webhook returned non-2xx |

---

## Key Files

| File | Role |
|---|---|
| `urap-app/src/pages/Revenue.tsx` | Frontend — method catalog, race trigger, results display |
| `server/main.py:1069–1107` | Route handlers: `POST /race/run`, `GET /race/results` |
| `modules/m4_inbound/race_agents.py` | `RaceAuction` — CPL auction engine |
| `modules/m4_inbound/marketplace_router.py` | `MarketplaceRouter` — catalog + webhook config |
| `modules/m4_inbound/lead_router.py` | `LeadRouterService` — inbound capture (prerequisite for leads pool) |
| `server/main.py:476–496` | `POST /outreach/intent/score` — lead scoring for auction input |
