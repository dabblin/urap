# urap-app

React + Vite frontend dashboard for the URAP platform. Built on the Seamless.AI three-column layout model. Talks directly to `urap-engine` over HTTP — no server-side rendering layer.

---

## Tech Stack

| Layer | Choice |
|---|---|
| Framework | React 19 + Vite 6 |
| Language | TypeScript 5.7 |
| Routing | React Router v7 |
| Styling | Tailwind CSS 3 |
| Port | 3034 (locked via `--strictPort`) |

---

## Getting Started

```bash
cd urap-app
cp .env.example .env   # optional — defaults work for local dev
npm install
npm run dev            # http://localhost:3034
```

The app expects `urap-engine` running at `http://localhost:8080`. Start the engine first:

```bash
# In urap-engine/
./start.sh
```

### Environment Variables

Create `.env` at the project root (never commit it):

```env
VITE_ENGINE_URL=http://localhost:8080   # default — change for staging/prod
VITE_TENANT_ID=local                    # tenant scope for all engine requests
VITE_USER_NAME=there                    # display name on the search hero screen
```

---

## Layout Architecture

The app follows a strict three-column layout:

```
┌──────────────────────────────────────────────────────────────┐
│  [Logo]  [Data Engine ▾]  [Engagement ▾]  [Automation ▾]  ⚙ │  TopNav
├─────────┬────────────────────────────────┬───────────────────┤
│ Sidebar │   Main Content / Data Grid      │  Detail Panel     │
│         │                                 │  (self-contained  │
│ ● tools │  Company / Name / Email / …     │   per page)       │
│   by    │  ────  ────  ────  ────  ────   │                   │
│ pillar  │  ────  ────  ────  ────  ────   │                   │
└─────────┴────────────────────────────────┴───────────────────┘
```

- **TopNav** — logo + three pillar dropdowns (Data Engine, Engagement Hub, Automation Network)
- **Sidebar** — tool list driven entirely by the `toolRegistry`; no hardcoded nav
- **Main content** — each page is self-contained; owns its own data-fetching and layout
- **Detail panel** — rendered inside the page component, not in the app shell

---

## Source Layout

```
src/
  App.tsx              Root router; mounts Sidebar + TopNav + page routes
  main.tsx             Entry point
  registry.ts          Tool registry (see "Adding a New Tool" below)
  types.ts             Shared TypeScript interfaces (UrapTool, ContactResult)
  assets/
    urap-logo.png      PNG logo displayed in TopNav

  components/layout/
    TopNav.tsx         Top navigation bar with pillar dropdowns
    Sidebar.tsx        Left sidebar; reads from toolRegistry
    DetailPanel.tsx    Reusable detail panel component (legacy — currently unused in shell)

  pages/
    CompaniesSearch.tsx   Full company search, enrichment, social discovery, list management
    Prospector.tsx        Contact prospector (ICP search)
    Emailing.tsx          Drip sequence management
    BuyerIntent.tsx       Intent-scored contact list
    JobChanges.tsx        Job-change signal monitor
    Connect.tsx           One-click find + add to sequence
    WarpMode.tsx          Warp Mode AI agent UI
    AutoPilot.tsx         Autopilot ICP runner UI
    ReplyIntel.tsx        Reply Intelligence inbox
    Calling.tsx           Twilio Power Dialer
    Integrations.tsx      Zapier webhook management
    ApiKeys.tsx           Developer API key management
    BulkEnrich.tsx        CSV/ICP bulk enrichment jobs
```

---

## Tool Registry

The sidebar and routing are driven entirely by `src/registry.ts`. No hardcoded nav.

### How to Add a New Tool

1. Create the page component in `src/pages/MyNewTool.tsx`
2. Register the tool in `src/registry.ts`:

```typescript
import { registerTool } from './registry.js';

registerTool({
  id:     'my-new-tool',
  label:  'My New Tool',
  pillar: 'data',          // 'data' | 'engagement' | 'automation'
  icon:   '🔍',
  route:  '/my-new-tool',
  sprint: 7,
});
```

3. Add the route to `App.tsx`:

```tsx
import { MyNewTool } from './pages/MyNewTool.js';
// …
<Route path="/my-new-tool" element={<MyNewTool />} />
```

The tool automatically appears in the Sidebar under the correct pillar. That is the only change required.

---

## Companies Search — Feature Reference

`CompaniesSearch.tsx` is the most complete page in the app. It demonstrates all major patterns.

### Search Modes

| Input | Behavior |
|---|---|
| Domain only | Single-company enrichment lookup |
| Name + Location | Filtered local business search |
| Keywords + Location | Multi-source local discovery (Google Places + Yelp + Foursquare) |
| Industry + Location | Industry-scoped search (industry value used as Yelp search term) |
| Free-text (AI Search hero) | Parses natural language: "barbershops in Atlanta" → keywords + location |

### Contact Enrichment

Click **Find Contact** on any row or **Enrich All** to run the discovery waterfall:

1. Yelp details API (if Yelp result) → real business website
2. Domain guessing from business name
3. Hunter.io domain-search (parallel with social scraping)
4. Homepage email scrape

Results appear inline: email address in the Email column, social badges (LinkedIn `in`, Instagram `ig`, Twitter `x`, YouTube `yt`) in the Socials column.

### Social Profile Icons

After enrichment, the **Socials** column shows compact colored badges linking directly to each found profile:

- `in` → LinkedIn company page
- `ig` → Instagram
- `x` → Twitter / X
- `yt` → YouTube channel or `@handle`

The detail panel shows the same links with full platform names when a row is selected.

### Outreach Actions

From the detail panel (after enrichment finds an email):
- **Send Email** → opens the Compose modal (single email via SMTP2GO → Brevo → Mailgun)
- **↪ Drip** → opens the 3-Step Drip Sequence builder (creates template + enrolls contact)

### Autopilot

The **⚡ Autopilot** button opens a one-shot ICP runner: set keywords, location, industry, pick an existing drip sequence, set max companies, and launch. The engine searches, enriches, and enrolls all found emails automatically.

### My Lists

**📁 Add to List** saves current search results + any enriched emails to a named Supabase list. Lists persist across sessions. From My Lists view, click any list to see its items and export as CSV.

---

## Key Component Patterns

### API Calls

All engine calls follow this pattern:

```typescript
const resp = await fetch(`${ENGINE_URL}/companies/search`, {
  method:  'POST',
  headers: {
    'Content-Type': 'application/json',
    'x-tenant-id': TENANT_ID,
    // 'x-api-key': API_KEY  ← add when key enforcement is enabled
  },
  body: JSON.stringify(payload),
});
const data = await resp.json();
```

`ENGINE_URL` and `TENANT_ID` are read from `import.meta.env.VITE_ENGINE_URL` and `VITE_TENANT_ID` at build time, with safe defaults for local dev.

### Enrichment State

Contact enrichment state is stored in `enrichMap: Record<number, EnrichedContact>` keyed by result row index. An `EnrichedContact` has a `status` field (`'loading' | 'found' | 'not_found'`) that drives all conditional rendering in the table and detail panel.

```typescript
interface EnrichedContact {
  email, first_name, last_name, title, confidence, source;
  status:    'loading' | 'found' | 'not_found';
  linkedin?, instagram?, twitter?, youtube?;  // social profiles from scraping
}
```

### Listing-Domain Guard

`isListingDomain(url)` prevents sending Yelp, Facebook, LinkedIn, etc. URLs to the enrichment API, which would always return no email. Applied to both `domain` and `website` fields before enrichment calls.

---

## Building for Production

```bash
npm run build     # outputs to dist/
npm run preview   # preview the production build locally
```

The `dist/` folder is a standard Vite static bundle — deployable to any static host (Vercel, Netlify, Cloud Run static, Nginx).

Set `VITE_ENGINE_URL` to the production engine URL at build time:

```bash
VITE_ENGINE_URL=https://urap-engine.run.app npm run build
```
