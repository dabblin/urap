# Route Tab (Anti-Gravity) — Complete Guide

> Admin-only. Access at **Navis → Route** in the BizReach Pro command center.  
> URL: `https://bizreach-command.bizreachpro.workers.dev` → Route tab

---

## What Is the Route Tab?

The Route tab is BizReach Pro's **lead monetization engine**. It connects the leads you've collected (from Finder, Whales, GMB, People, etc.) to external buyer marketplaces that pay cash per lead.

Every contact in your database with a score above your threshold can be routed to a buyer who pays $20–$260 per lead. The Route tab automates this entire process.

**Core loop:**
```
Your Contacts DB → Score & Qualify → Route to Buyers → Receive Payment
```

---

## Income Potential

| Configuration | Monthly Potential |
|---|---|
| 100 leads/mo @ $45 avg CPL | $4,500/mo |
| 500 leads/mo @ $60 avg CPL | $30,000/mo |
| 2,000 leads/mo @ $80 avg CPL (Ping/Post) | $160,000/mo |
| Full auto-router + multiple marketplaces | $12,500–$80,000/mo |

---

## Marketplace Directory (18 Pre-Loaded)

All 18 buyer marketplaces are pre-loaded. Add your webhook URL + API key from each to activate.

| Marketplace | CPL Range | Best For | Docs |
|---|---|---|---|
| **PX Marketplace** | $30–$150 | Real-time Ping/Post bidding, all verticals | [px.com](https://www.px.com/publishers/) |
| **LeadsMarket** | $25–$260 | Finance & lending, AI-powered routing | [leadsmarket.com](https://www.leadsmarket.com) |
| **LeadPoint** | $20–$100 | World's largest leads exchange | [leadpoint.com](https://www.leadpoint.com) |
| **LeadExec / ClickPoint** | $40–$120 | Enterprise XML + Ping/Post distribution | [clickpointsoftware.com](https://www.clickpointsoftware.com) |
| **LeadCrowd** | $30–$120 | Mortgage & financial advisors | [leadcrowd.com](https://www.leadcrowd.com) |
| **Referr** | $20–$90 | 900+ categories, full transparency | [referr.co](https://www.referr.co) |
| **LeadNinja** | $25–$60 | Individual reps & small teams | [leadninja.com](https://www.leadninja.com) |
| **Oversource** | $30–$80 | Pay-later and pay-% of profit options | [oversource.io](https://www.oversource.io) |
| **Elite Lead Exchange** | $20–$50 | Free & transparent exchange platform | [eliteleadexchange.com](https://www.eliteleadexchange.com) |
| **SaleSpread** | $15–$40 | Quick sales for leads your team won't pursue | [salespread.io](https://www.salespread.io) |
| **Leadfellow** | $25–$65 | B2B partner network, trusted circles | [leadfellow.com](https://www.leadfellow.com) |
| **LeadSwap** | $25–$55 | Upload verified lists, keep 76% | [leadswap.io](https://www.leadswap.io) |
| **CloudTask Marketplace** | $40–$80 | Sales outsourcing & remote agencies | [marketplace.cloudtask.com](https://marketplace.cloudtask.com) |
| **E-prospects.biz** | $20–$50 | eBay-style lead marketplace | [e-prospects.biz](https://www.e-prospects.biz) |
| **GoTradeLeads** | $10–$30 | Free B2B trade leads, global buyers | [gotradelead.com](https://www.gotradelead.com) |
| **Serchz** | $30–$70 | B2B lead gen SaaS infrastructure | [serchz.com](https://www.serchz.com) |
| **Premier Business Club** | $15–$35 | Regional/language-sorted trade leads | [premierbusinessclub.com](https://www.premierbusinessclub.com) |
| **Custom / Agency** | $150+ | Your own buyers — premium direct webhook | —configure your webhook URL— |

---

## Core Features

### 1. Lead Selector & Filters

Before routing, you filter and select which contacts to send:

| Filter | Description |
|---|---|
| **Min Score** | Only route contacts above a quality threshold (0–100). Score 60+ recommended. |
| **Has Email** | Only route contacts with a verified email address. Increases CPL 2–3× on finance platforms. |
| **Hide Routed** | Exclude contacts already sent to a buyer. Prevents duplicates. |
| **Category Filter** | Route only specific verticals (HVAC, legal, dental, etc.) to the matching marketplace. |

**Lead scoring** is automatic based on: has website (+20), has phone (+15), has email (+25), rating > 4.0 (+10), category match (+10).

---

### 2. Route Modes

#### Standard Route
Send selected leads to one marketplace via their webhook URL.
- Select contacts → choose platform → click **Route Selected**
- Webhook sends JSON payload with name, email, phone, city, state, category, score
- Result logged with platform name, lead count, and estimated earnings

#### Ping/Post Mode (Toggle)
Sends leads to **all configured platforms simultaneously** and collects the highest bid.
- Toggle **Ping/Post** on before routing
- All platforms with webhook URLs receive the lead
- Platform that responds fastest with the highest CPL wins
- Remaining platforms receive a "post" with the accepted data

---

### 3. AI Lead Qualification

Before routing, the AI qualifies each lead against TCPA compliance + intent signals.

```
Qualify Selected → Claude AI scores each lead 0–100
→ Grade: A (80+), B (60–79), C (40–59), D (<40)
→ Disqualified leads are hidden from routing queue
```

**TCPA Compliance:** The Route tab enforces CAN-SPAM and TCPA acknowledgment before your first routing session. You must confirm consent compliance.

---

### 4. Auto-Router

Set-it-and-forget-it automated lead routing.

**Configure:**
- **Score threshold** — only route leads above this score (default: 60)
- **Interval** — how often to auto-route: 5 min / 15 min / 1 hr / 6 hr
- **Platform** — which marketplace receives the leads
- **Auto-Qualify** — run AI scoring before each batch
- **Auto-Enrich** — run email finder before routing (increases CPL 2–3×)

**How to start:**
1. Configure a marketplace webhook URL
2. Set score threshold and interval
3. Toggle **Auto-Router ON**
4. Countdown timer shows next scheduled run
5. Each run is logged with leads sent + earnings

The auto-router persists in `localStorage` and survives page refreshes. It pauses when the tab is closed.

---

### 5. Bulk Sweep

Automatically discovers and loads leads from all US states and high-CPL categories:

**High-CPL categories auto-targeted:**
- Contractors, Law, Medical, Real Estate, Auto, Restaurants, Gyms, Salons

**Process:**
1. Click **Bulk Sweep** → selects 10 states × 3 cities × all categories
2. Searches Google Places + OSM + Yelp for each combination
3. Saves discovered leads to contacts DB
4. Pre-selects newly discovered leads for immediate routing

Estimated: **1,200–2,400 leads per sweep batch**.

---

### 6. Race Agents (CPL Auction)

Run a real-time auction across all configured marketplaces to find who pays the most per lead.

```
Race Agents → sends sample leads to all platforms simultaneously
→ Measures response time + CPL offered by each
→ Recommends optimal routing order
→ Locks in highest-paying buyer per vertical
```

Typically increases CPL by **2–3× vs flat routing**.

---

### 7. Revenue Goal & Projections

Set a monthly income target and the tab calculates what you need:

**Inputs:**
- Monthly income goal (default: $100,000)
- Current marketplaces configured (webhook URLs added)
- Average CPL across active platforms

**Output:**
- Leads needed per day to hit goal
- Recommended auto-route interval
- Best platform recommendation
- One-click: **Configure Auto-Router for $X/mo**

**Revenue Projections panel** shows:
- Projected monthly at current routing rate
- Leads to route per day to hit goal
- Break-even point

---

### 8. Pipeline Funnel

Visual breakdown of your full lead pipeline:

```
Found → Contacted → Opened → Clicked → Replied → Routed → Earned
```

Shows conversion rates at each stage and identifies the biggest drop-off point.

---

### 9. Earnings Chart

Bar chart of routing revenue over the last 30 days:
- Revenue from webhook routing sessions
- Revenue from appointments (set, showed, closed)
- Combined total with daily breakdown

---

### 10. Appointments Tracker

Track high-value appointment outcomes alongside routing revenue:

| Field | Description |
|---|---|
| **Contact Name** | Who the appointment is with |
| **Source** | How they were found (Finder, Whales, LinkedIn, etc.) |
| **Status** | Set → Showed → Closed or No-Show |
| **Value** | Dollar value of the appointment ($500 default) |

Closed appointments add to your total Revenue Dashboard alongside routing earnings.

---

### 11. Buyer Inbox

Monitor incoming buyer replies and manage pipeline:

**Filters:** All / Hot / Replied / New

| Status | Meaning |
|---|---|
| 🔥 Hot Lead | Buyer replied with interest — immediate action needed |
| 💛 Replied | Buyer responded — follow up within 24 hours |
| 🔵 Buyer Inquiry | New inquiry from a potential lead buyer |
| 🟣 Prospect | Warming up, not yet confirmed |

**Gmail Integration:** Direct link to Gmail filtered to last 3 days of inbox.

---

### 12. Find & Pitch Real Buyers

Automatically discovers businesses that buy leads in your verticals:

1. Searches Serper for lead buyers in each category
2. Generates personalized pitch emails
3. Sends pitches via configured email sender
4. Logs all outreach to activity_log

Export as CSV for manual follow-up if preferred.

---

### 13. Social Posts Generator

Generates LinkedIn/Facebook social proof posts from routing results:

```
"We just routed 47 qualified HVAC leads across Atlanta → 3 buyers competed → avg CPL: $68. Here's how..."
```

5 posts generated per run, ready to copy-paste. Builds credibility for attracting more buyers.

---

### 14. Form Filler Agent

Automates signing up for new marketplace accounts:

- Reads marketplace documentation pages via Firecrawl
- Generates auto-fill data for publisher applications
- Creates a pre-filled application template
- Reduces manual signup time from 30 min → 5 min per platform

---

### 15. Cron Pipeline (Automated Scheduling)

Two scheduled jobs run automatically:

| Cron | Schedule | What It Does |
|---|---|---|
| `runPipelineNow` | Every 6 hours | Sweeps new leads + qualifies + routes |
| `sendDailySummary` | Daily at 8 AM | Emails earnings summary to operator |

**Cron History panel** shows:
- Last 10 automated runs
- Leads swept, qualified, routed per run
- Earnings per run
- Any errors

Trigger a manual cron run with **Run Pipeline Now**.

---

### 16. Sync Contact Scores

Recalculates quality scores for all contacts in the database:

- Runs `scoreLead()` on every contact
- Updates `contacts.score` in Supabase
- Updates `contacts.status` (new/contacted/opened/hot_lead)
- Refreshes the lead queue with updated rankings

Run before a routing session to ensure the highest-quality leads go first.

---

### 17. Marketplace Configuration

Each marketplace card has:

| Field | Description |
|---|---|
| **Webhook URL** | The POST endpoint the marketplace gives you. Required. |
| **API Key** | Optional auth token for the webhook. |
| **CPL** | Your target cost-per-lead. Used for earnings calculations. |
| **Test Webhook** | Sends a sample payload to verify connectivity before live routing. |

Changes auto-save to Supabase and localStorage.

---

## Webhook Payload Format

All marketplace webhooks receive this JSON payload:

```json
{
  "first_name": "Kenny",
  "last_name": "Mitchell",
  "business_name": "Atlanta HVAC Pro",
  "email": "info@atlantahvacpro.com",
  "phone": "404-555-1234",
  "address": "123 Main St",
  "city": "Atlanta",
  "state": "GA",
  "zip": "30301",
  "category": "HVAC",
  "score": 78,
  "source": "BizReach Pro",
  "timestamp": "2026-06-02T14:30:00Z"
}
```

---

## Revenue Tracking

All routing sessions are logged with:
- Platform name
- Lead count routed
- Estimated earnings (count × CPL)
- Timestamp
- Success / error status

**Total earnings** shown in the Revenue Dashboard combines:
1. Webhook routing revenue
2. Appointment closed values
3. Historical log totals

---

## Quick Start (Make First $$$)

1. **Sign up for PX Marketplace** → [px.com/publishers](https://www.px.com/publishers/)
2. **Get your webhook URL** from PX dashboard
3. **Paste webhook URL** into the PX Marketplace card in Route tab
4. **Click Test Webhook** → should return 200 OK
5. **Set score threshold to 60**
6. **Select all contacts** with score > 60 + has email
7. **Click Route Selected** → leads sent, earnings logged
8. **Enable Auto-Router** at 1-hour intervals for passive income

---

## Connecting to NetNavis

The Route tab is step 11 in the 22-agent Relay Pipeline:

```
ElecMan.EXE → Route tab → Bass.EXE (max CPL auction)
```

- **ElecMan.EXE** — tests all webhooks, routes leads to all configured platforms
- **Bass.EXE** — runs the CPL auction, selects highest bidder per lead

Trigger from **Navis → Relay Pipeline → Step 11 (Webhook Routing)**.

---

## Files

| File | Purpose |
|---|---|
| `src/components/biz/AntiGravityTab.tsx` | Full Route tab component (1,800+ lines) |
| `src/lib/biz.functions.ts` | Server functions: `routeLeadsWebhook`, `qualifyLeads`, `testWebhook`, `bulkSweepLeads`, `runRaceAgents`, `syncContactScores`, `markLeadsRouted`, `exportLeadsCsvData`, `findAndPitchRealBuyers`, `runPipelineNow`, `getCronHistory` |
| `src/routes/api/cron/pipeline.ts` | Scheduled cron job for automated routing |
| `src/lib/mmbn-agents.ts` | ElecMan.EXE + Bass.EXE agent logic |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| **"No destinations have a webhook URL"** | Add a webhook URL to at least one marketplace card |
| **TCPA dialog appears** | Read + acknowledge TCPA compliance before first routing session |
| **Webhook test fails (4xx)** | Check the webhook URL format — must include `https://` |
| **0 leads in queue** | Run Finder tab first, or click Bulk Sweep to discover new leads |
| **Low earnings** | Enable Auto-Qualify + Auto-Enrich in Auto-Router settings (raises CPL 2–3×) |
| **Auto-router not running** | Auto-router pauses when tab is closed. Keep browser open or use cron. |
