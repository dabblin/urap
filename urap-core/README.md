# @antigravity/urap-core

Express middleware plugin for the URAP platform. Install this package on any Express-based host application to embed URAP lead capture, outreach webhooks, and consent recording — without deploying a separate frontend.

---

## Concept

`urap-core` is a thin proxy layer. It exposes a set of URAP-flavored HTTP routes on the host app, then forwards every call to the `urap-engine` microservice with the correct tenant credentials injected. The host application never handles URAP business logic directly.

```
Host App (Express)
  └── app.use('/urap', urapMiddleware({ apiKey, tenantId }))
            │
            └── proxies to urap-engine :8080
```

---

## Installation

```bash
npm install @antigravity/urap-core
# or: yarn add @antigravity/urap-core
```

Requires Node.js 18+ and Express 4.18+.

---

## Quick Start

```typescript
import express from 'express';
import { urapMiddleware } from '@antigravity/urap-core';

const app = express();
app.use(express.json());

app.use('/urap', urapMiddleware({
  apiKey:    process.env.URAP_API_KEY!,   // tenant API key from /api/keys
  tenantId:  'client-xyz',                 // your client identifier
  engineUrl: process.env.URAP_ENGINE_URL,  // default: http://localhost:8080
}));

app.listen(3000);
```

Once mounted, the following routes are available on the host app:

| Method | Path | Description |
|---|---|---|
| `GET` | `/urap/status` | Health + config check |
| `POST` | `/urap/leads/capture` | Inbound lead capture (called by embed form) |
| `GET` | `/urap/leads/preview/:id` | Get anonymized preview attributes (ping-post) |
| `POST` | `/urap/leads/claim` | Claim full PII for a previewed lead |
| `GET` | `/urap/leads/recent` | List recently captured leads |
| `POST` | `/urap/outreach/event` | Channel state event (reply, send, open, bounce, etc.) |
| `POST` | `/urap/webhooks/:module` | Receive delivery callbacks from SMTP2GO / Twilio |
| `POST` | `/urap/consent` | Record a TrustedForm consent certificate |
| `GET` | `/urap/embed.js` | Serves the inbound lead capture form snippet |

---

## Configuration

```typescript
interface UrapConfig {
  apiKey:    string;   // tenant API key — get one from urap-engine /api/keys
  tenantId:  string;   // unique identifier for this client/tenant
  engineUrl?: string;  // engine base URL (default: 'http://localhost:8080')
}
```

---

## Inbound Lead Capture Embed

URAP provides a self-contained lead capture form that any host page can embed. No React or build tools required on the host site.

### Step 1 — Add the script tag

```html
<script src="/urap/embed.js"></script>
```

### Step 2 — Add a mount point

```html
<div data-urap-form></div>
```

The embed script automatically renders a styled form into every `[data-urap-form]` element on the page. The form fields are: First Name, Last Name, Work Email (required), Company, plus any extras you configure.

### Step 3 — (Optional) Add TrustedForm for TCPA compliance

```html
<!-- Include TrustedForm before the embed script -->
<script type="text/javascript">
  (function() {
    var tf = document.createElement('script');
    tf.type = 'text/javascript'; tf.async = true;
    tf.src = 'https://api.trustedform.com/trustedform.js?field=xxTrustedFormCertUrl';
    document.head.appendChild(tf);
  })();
</script>
<script src="/urap/embed.js"></script>
<div data-urap-form></div>
```

When TrustedForm is present, the embed automatically captures the cert URL and sends it to `/urap/consent` on form submission. The consent record is stored insert-only in the URAP consent ledger.

### Customizing the Form

The embed snippet is generated from `UrapConfig` options. To customize labels and fields, modify the `generateEmbedSnippet` call inside `middleware.ts`, or pass override options when mounting.

Default form behavior:
- Submits JSON to `/urap/leads/capture`
- Shows success message on completion
- Re-enables submit button on network error

---

## Type Reference

### `LeadStatusObject`

The core data model shared across all URAP modules:

```typescript
interface LeadStatusObject {
  leadId:    string;
  tenantId:  string;
  contactData: {
    name, email, phone?, linkedinUrl?, company, title, intentSignals: string[];
  };
  channelState: {
    email:    'idle' | 'sent' | 'opened' | 'replied' | 'bounced' | 'paused';
    sms:      'idle' | 'sent' | 'replied' | 'opted_out' | 'paused';
    linkedin: 'idle' | 'connected' | 'messaged' | 'replied' | 'paused';
    voice:    'idle' | 'dialed' | 'answered' | 'voicemail' | 'paused';
  };
  globalStatus:
    | 'prospecting' | 'engaged' | 'interested' | 'meeting_set'
    | 'qualified'   | 'not_interested' | 'unsubscribe';
  lastActivity:   string;
  assignedAgent?: string;
  consentRecord?: {
    source: string; consentedAt: string; ipAddress: string;
    oneToOneRule: boolean; platformName: string;
  };
}
```

### `UrapTool`

Registered in `registry.ts` to drive dynamic sidebar and routing:

```typescript
interface UrapTool {
  id:          string;   // 'prospector', 'buyer-intent', etc.
  label:       string;   // display name
  pillar:      'data' | 'engagement' | 'automation';
  icon:        string;   // emoji or icon name
  route:       string;   // '/prospector'
  featureFlag?: string;  // optional gate
  sprint:      number;   // sprint that delivered this tool
}
```

---

## Tool Registry

The registry is used by `urap-app` to build the sidebar and routing dynamically. It can also be used in host applications to query available tools.

```typescript
import { registerTool, getAllTools, getToolsByPillar, getToolById } from '@antigravity/urap-core';

// Register a new tool (called once at startup in the sprint that adds it)
registerTool({
  id: 'custom-report', label: 'Custom Report',
  pillar: 'data', icon: '📊', route: '/custom-report', sprint: 7,
});

// Query
getAllTools();                   // all registered tools
getToolsByPillar('data');        // tools in the Data Engine pillar
getToolById('prospector');       // single tool lookup
```

---

## Building and Publishing

```bash
# Development
npm run dev          # tsx watch mode

# Build for distribution
npm run build        # compiles TypeScript to dist/
npm run prepublishOnly   # build runs automatically before npm publish
```

The `dist/` folder and `src/` are included in the published package. TypeScript consumers get `.d.ts` type declarations automatically.

---

## Security Considerations

- **API key handling:** The `apiKey` passed to `urapMiddleware` is injected into every proxied engine request as `x-api-key`. Keep it in an environment variable — never hardcode it.
- **Consent endpoint:** `/urap/consent` accepts unauthenticated POSTs (the embed form has no API key). The engine validates `tenant_id` in the body against known tenants.
- **Lead capture:** `/urap/leads/capture` is also public. Rate limiting should be applied at the host application or load-balancer level.
- **TCPA gate:** Before queuing any SMS or voice outreach through `/urap/outreach/event`, verify consent exists via `POST /consent/check` on the engine directly. The middleware does not enforce this automatically.
