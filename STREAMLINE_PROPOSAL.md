# URAP Streamline Proposal — Open-Ended Discovery Core
**Date:** 2026-07-07 | **Author:** CIO agent | **Status:** AWAITING CEO SIGN-OFF

## What URAP actually is today (measured, not guessed)
- **Engine** (`urap-engine`, FastAPI :8080 local / Cloud Run prod): **68 endpoints**, 6 modules (~4,600 LOC), 14 tier3 connectors.
- **App** (`urap-app`, Vite SPA :3035): pure frontend — it has no API of its own; everything hits the engine.
- The Bronx pipeline now pushes into URAP via `POST /companies/list/save` (verified live: 42-item list "Bronx AI Prospects — 2026-07-07").

## The bloat (proposed cuts)
| Cut | Evidence | Endpoints freed |
|---|---|---|
| `tier3/hubspot`, `tier3/salesforce` | **Empty directories — zero code** | 0 (never wired) |
| Zapier integration | 3 endpoints, no active zaps | 3 |
| Duplicate email senders: keep **Brevo**, drop `mailgun`, `smtp2go` | 3 senders for 1 job | — |
| Marketplace router + Race auction (`m4_inbound` race/route/dispatch) | $0 revenue, blocked on publisher signups since Sprint 8 — park, don't maintain | ~9 |
| Autopilot + drip sequences (`m5_api/autopilot_runner`, sequence endpoints) | No sequences running; premature until first closed client | ~9 |
| API key manager self-service (`/api/keys` CRUD) | Single-tenant reality (`dev-tenant`) | 3 |

Net: **~25 of 68 endpoints retired**, engine drops to a core anyone can hold in their head.

## The keep — Discovery Core
1. **Discover** — `POST /companies/search` (Apollo + Google Places + Yelp + Foursquare in parallel). Already open-ended: any keywords × any location × any industry.
2. **Score** — NEW `POST /companies/score`: port the Bronx pipeline's Haiku AI-readiness scorer + Crawl4AI site read into `m1_intelligence`. Discovery without qualification is noise.
3. **Enrich** — `/enrich`, `/companies/contact` (Prospeo → Snov → Hunter waterfall). Keep.
4. **Reach** — `/outreach/email/send` (Brevo), `/voice/dial` + `/sms/send` (Twilio). Keep — phone-first matters: **today `/campaigns` silently drops every contact without an email**, which is exactly our Bronx list. Fix: campaigns get a `channel: email|call|sms` field; call campaigns render scripts, not templates.
5. **Lists + Campaigns** — keep, with the phone-channel fix above.

## Result
URAP becomes: **Discover → Score → Enrich → Reach**, one screen per verb, any market not just Bronx. The `bronx_ai_prospect_pipeline.py` script becomes a thin client of URAP instead of a parallel system.

## Decision needed from CEO
- [ ] Approve the 6 cuts above (code parked in a `retired/` branch, not deleted)
- [ ] Approve porting scorer into the engine (`/companies/score`)
- [ ] Approve call-channel campaigns (unlocks the 34 phone-only Bronx leads inside URAP)
