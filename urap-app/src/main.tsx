import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App.js';
import { registerTool } from './registry.js';

// Sprint 1
registerTool({ id: 'prospector',      label: 'Contacts',         pillar: 'data', icon: '🔍', route: '/prospector', sprint: 1 });
registerTool({ id: 'company-search',  label: 'Companies',        pillar: 'data', icon: '🏢', route: '/companies',  sprint: 1 });

// Sprint 3
registerTool({ id: 'buyer-intent', label: 'Buyer Intent', pillar: 'data', icon: '🎯', route: '/buyer-intent', sprint: 3 });
registerTool({ id: 'job-changes', label: 'Job Changes', pillar: 'data', icon: '💼', route: '/job-changes', sprint: 3 });
registerTool({ id: 'connect', label: 'Connect', pillar: 'engagement', icon: '⚡', route: '/connect', sprint: 3 });
registerTool({ id: 'emailing', label: 'Emailing', pillar: 'engagement', icon: '✉️', route: '/emailing', sprint: 3 });

// Sprint 4
registerTool({ id: 'warp-mode', label: 'Warp Mode', pillar: 'automation', icon: '⚡', route: '/warp-mode', sprint: 4 });
registerTool({ id: 'autopilot', label: 'Autopilot', pillar: 'automation', icon: '🤖', route: '/autopilot', sprint: 4 });
registerTool({ id: 'reply-intel', label: 'Reply Intel', pillar: 'automation', icon: '🧠', route: '/reply-intel', sprint: 4 });
registerTool({ id: 'analytics', label: 'Analytics', pillar: 'automation', icon: '📊', route: '/analytics', sprint: 4 });

// Sprint 5
registerTool({ id: 'calling', label: 'Calling', pillar: 'engagement', icon: '📞', route: '/calling', sprint: 5 });

// Sprint 6
registerTool({ id: 'integrations', label: 'Integrations', pillar: 'engagement', icon: '🔗', route: '/integrations', sprint: 6 });
registerTool({ id: 'api-keys', label: 'API', pillar: 'automation', icon: '🔑', route: '/api-keys', sprint: 6 });
registerTool({ id: 'bulk-credits', label: 'Bulk Credits', pillar: 'automation', icon: '📦', route: '/bulk-credits', sprint: 6 });

// Sprint 7 — BizReach Route Tab integration
registerTool({ id: 'lead-router', label: 'Lead Router', pillar: 'automation', icon: '💰', route: '/lead-router', sprint: 7 });

// Sprint 8 — BizReach Money Tab integration
registerTool({ id: 'revenue', label: 'Revenue', pillar: 'automation', icon: '💵', route: '/revenue', sprint: 8 });

// Sprint 9A — Batch Email Campaigns
registerTool({ id: 'campaigns', label: 'Campaigns', pillar: 'engagement', icon: '📨', route: '/campaigns', sprint: 9 });

// Sprint 9B — Campaign Landing Pages
registerTool({ id: 'landing-pages', label: 'Landing Pages', pillar: 'engagement', icon: '🌐', route: '/landing-pages', sprint: 9 });

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
