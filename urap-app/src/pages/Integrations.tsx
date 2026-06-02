import { useState, useEffect } from 'react';

const ENGINE = 'http://localhost:8080';
const TENANT = 'dev-tenant';
const API_KEY = '';

function headers() {
  return { 'Content-Type': 'application/json', 'x-api-key': API_KEY, 'x-tenant-id': TENANT };
}

// ── Zapier types ──────────────────────────────────────────────────────────────

const GLOBAL_STATUS_EVENTS = [
  'prospecting', 'engaged', 'interested', 'meeting_set',
  'qualified', 'not_interested', 'unsubscribe',
];

interface Webhook {
  id: string;
  event: string;
  url: string;
  name: string;
  active: boolean;
  created_at: string;
}

// ── Marketplace types ─────────────────────────────────────────────────────────

interface Marketplace {
  id: string;
  name: string;
  cpl_range: string;
  best_for: string;
  webhook_url: string;
  api_key: string;
  cpl: number;
  configured: boolean;
}

// ── Zapier section ────────────────────────────────────────────────────────────

function ZapierSection() {
  const [webhooks, setWebhooks] = useState<Webhook[]>([]);
  const [event, setEvent] = useState('meeting_set');
  const [url, setUrl] = useState('');
  const [name, setName] = useState('');
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => { fetchWebhooks(); }, []);

  async function fetchWebhooks() {
    setLoading(true);
    try {
      const res = await fetch(`${ENGINE}/integrations/zapier`, { headers: headers() });
      const data = await res.json();
      setWebhooks(data.subscriptions || []);
    } catch (err) {
      console.error('[integrations/zapier] fetch error', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleSubscribe() {
    if (!url.trim()) return;
    setSaving(true);
    try {
      await fetch(`${ENGINE}/integrations/zapier/subscribe`, {
        method: 'POST',
        headers: headers(),
        body: JSON.stringify({ event, url: url.trim(), name: name.trim() || undefined }),
      });
      setUrl('');
      setName('');
      await fetchWebhooks();
    } catch (err) {
      console.error('[integrations/zapier] subscribe error', err);
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: string) {
    try {
      await fetch(`${ENGINE}/integrations/zapier/${id}`, {
        method: 'DELETE',
        headers: headers(),
      });
      setWebhooks(prev => prev.filter(w => w.id !== id));
    } catch (err) {
      console.error('[integrations/zapier] delete error', err);
    }
  }

  return (
    <div className="flex flex-col md:flex-row gap-4 h-full">
      {/* Subscribe form */}
      <div className="w-full md:w-80 md:flex-shrink-0 flex flex-col gap-3">
        <div>
          <p className="text-xs text-gray-500 mt-1">
            Zapier webhooks fire on every globalStatus change — connect 6,000+ tools.
          </p>
        </div>

        <div className="rounded border border-gray-800 bg-gray-900 px-4 py-3 space-y-3">
          <p className="text-xs text-gray-400 font-medium uppercase tracking-wider">New Webhook</p>

          <select
            className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
            value={event}
            onChange={e => setEvent(e.target.value)}
          >
            {GLOBAL_STATUS_EVENTS.map(ev => (
              <option key={ev} value={ev}>{ev}</option>
            ))}
          </select>

          <input
            className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
            placeholder="Zapier webhook URL *"
            value={url}
            onChange={e => setUrl(e.target.value)}
          />

          <input
            className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
            placeholder="Label (optional)"
            value={name}
            onChange={e => setName(e.target.value)}
          />

          <button
            onClick={handleSubscribe}
            disabled={saving || !url.trim()}
            className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white text-sm font-medium rounded px-4 py-2 transition-colors"
          >
            {saving ? 'Saving…' : '+ Subscribe'}
          </button>
        </div>

        <div className="text-xs text-gray-600 space-y-1">
          <p>Payload: event + tenant_id + lead_id + channel</p>
          <p>Fires on: /outreach/channel/event updates</p>
          <p>Zapier → HubSpot, Salesforce, Slack, +6,000 apps</p>
        </div>
      </div>

      {/* Webhook list */}
      <div className="flex-1 flex flex-col gap-2 overflow-auto">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Active Webhooks</h3>
          <button onClick={fetchWebhooks} className="text-xs text-gray-500 hover:text-gray-300">↻ refresh</button>
        </div>

        {loading && <p className="text-gray-600 text-sm">Loading…</p>}
        {!loading && webhooks.length === 0 && (
          <p className="text-gray-600 text-sm">No webhooks configured yet.</p>
        )}

        {webhooks.map(wh => (
          <div key={wh.id} className="rounded border border-gray-800 bg-gray-900 px-4 py-3 text-sm">
            <div className="flex justify-between items-start gap-3">
              <div className="flex flex-col gap-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="bg-indigo-900 text-indigo-300 text-xs px-2 py-0.5 rounded-full flex-shrink-0">
                    {wh.event}
                  </span>
                  {wh.name && <span className="text-gray-400 text-xs truncate">{wh.name}</span>}
                </div>
                <p className="text-gray-500 text-xs font-mono truncate">{wh.url}</p>
                <p className="text-gray-600 text-xs">{new Date(wh.created_at).toLocaleDateString()}</p>
              </div>
              <button
                onClick={() => handleDelete(wh.id)}
                className="text-gray-600 hover:text-red-400 text-xs flex-shrink-0 transition-colors"
              >
                remove
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Marketplace card ──────────────────────────────────────────────────────────

function MarketplaceCard({ mp, onSaved }: { mp: Marketplace; onSaved: () => void }) {
  const [expanded, setExpanded] = useState(false);
  const [webhookUrl, setWebhookUrl] = useState(mp.webhook_url || '');
  const [apiKey, setApiKey] = useState(mp.api_key || '');
  const [cpl, setCpl] = useState(mp.cpl || 0);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; status_code: number; error: string } | null>(null);

  async function handleSave() {
    setSaving(true);
    try {
      await fetch(`${ENGINE}/route/marketplace/${mp.id}`, {
        method: 'POST',
        headers: headers(),
        body: JSON.stringify({ webhook_url: webhookUrl, api_key: apiKey, cpl }),
      });
      onSaved();
      setExpanded(false);
    } catch (err) {
      console.error('[integrations/marketplace] save error', err);
    } finally {
      setSaving(false);
    }
  }

  async function handleTest() {
    setTesting(true);
    setTestResult(null);
    try {
      const res = await fetch(`${ENGINE}/route/test-webhook`, {
        method: 'POST',
        headers: headers(),
        body: JSON.stringify({ webhook_url: webhookUrl, api_key: apiKey }),
      });
      const data = await res.json();
      setTestResult(data);
    } catch {
      setTestResult({ success: false, status_code: 0, error: 'Network error' });
    } finally {
      setTesting(false);
    }
  }

  return (
    <div className={`rounded border transition-colors ${mp.configured ? 'border-emerald-800 bg-emerald-950/10' : 'border-gray-800 bg-gray-900'}`}>
      <div
        className="flex items-center gap-3 px-3 py-2.5 cursor-pointer"
        onClick={() => setExpanded(v => !v)}
      >
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <p className="text-sm text-white font-medium truncate">{mp.name}</p>
            {mp.configured && (
              <span className="text-xs bg-emerald-900 text-emerald-300 px-1.5 py-0.5 rounded-full flex-shrink-0">
                configured
              </span>
            )}
          </div>
          <p className="text-xs text-gray-500 truncate">{mp.cpl_range} · {mp.best_for}</p>
        </div>
        <span className="text-gray-600 text-xs flex-shrink-0">{expanded ? '▲' : '▼'}</span>
      </div>

      {expanded && (
        <div className="border-t border-gray-800 px-3 py-3 space-y-2">
          <input
            className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500 font-mono"
            placeholder="Webhook URL (https://…) *"
            value={webhookUrl}
            onChange={e => setWebhookUrl(e.target.value)}
          />
          <input
            className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500"
            placeholder="API Key (optional)"
            value={apiKey}
            onChange={e => setApiKey(e.target.value)}
          />
          <div className="flex items-center gap-2">
            <label className="text-xs text-gray-400 w-24 flex-shrink-0">CPL Target ($)</label>
            <input
              type="number" min={0} step={5}
              className="bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-xs text-white w-full focus:outline-none focus:border-emerald-500"
              value={cpl}
              onChange={e => setCpl(parseFloat(e.target.value) || 0)}
            />
          </div>

          {testResult && (
            <p className={`text-xs ${testResult.success ? 'text-emerald-400' : 'text-red-400'}`}>
              {testResult.success
                ? `✓ Webhook OK (HTTP ${testResult.status_code})`
                : `✗ ${testResult.error || `HTTP ${testResult.status_code}`}`}
            </p>
          )}

          <div className="flex gap-2 pt-1">
            <button
              onClick={handleTest}
              disabled={testing || !webhookUrl.trim()}
              className="flex-1 bg-gray-700 hover:bg-gray-600 disabled:opacity-40 text-white text-xs font-medium rounded px-3 py-1.5 transition-colors"
            >
              {testing ? 'Testing…' : 'Test Webhook'}
            </button>
            <button
              onClick={handleSave}
              disabled={saving || !webhookUrl.trim()}
              className="flex-1 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 text-white text-xs font-medium rounded px-3 py-1.5 transition-colors"
            >
              {saving ? 'Saving…' : 'Save'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Marketplaces section ──────────────────────────────────────────────────────

function MarketplacesSection() {
  const [marketplaces, setMarketplaces] = useState<Marketplace[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { fetchMarketplaces(); }, []);

  async function fetchMarketplaces() {
    setLoading(true);
    try {
      const res = await fetch(`${ENGINE}/route/marketplaces`, { headers: headers() });
      const data = await res.json();
      setMarketplaces(data.marketplaces || []);
    } catch (err) {
      console.error('[integrations/marketplaces] fetch error', err);
    } finally {
      setLoading(false);
    }
  }

  const configuredCount = marketplaces.filter(m => m.configured).length;

  return (
    <div className="flex flex-col gap-3 h-full overflow-auto">
      <div className="flex items-center justify-between flex-shrink-0">
        <div>
          <p className="text-xs text-gray-500">
            18 pre-loaded buyer marketplaces. Add a webhook URL to activate any marketplace.
            {configuredCount > 0 && (
              <span className="text-emerald-400 ml-1">{configuredCount} configured.</span>
            )}
          </p>
        </div>
        <button onClick={fetchMarketplaces} className="text-xs text-gray-500 hover:text-gray-300 flex-shrink-0">
          ↻ refresh
        </button>
      </div>

      {loading && <p className="text-gray-600 text-sm">Loading marketplaces…</p>}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-2">
        {marketplaces.map(mp => (
          <MarketplaceCard key={mp.id} mp={mp} onSaved={fetchMarketplaces} />
        ))}
      </div>

      <div className="text-xs text-gray-600 space-y-1 pt-2 border-t border-gray-800 flex-shrink-0">
        <p>CPL target is used for earnings estimates in Lead Router — not enforced at the marketplace level.</p>
        <p>Configured marketplaces are available in Lead Router → Route To dropdown.</p>
      </div>
    </div>
  );
}

// ── Main Integrations page ────────────────────────────────────────────────────

type Tab = 'zapier' | 'marketplaces';

export function Integrations() {
  const [tab, setTab] = useState<Tab>('zapier');

  return (
    <div className="flex flex-col p-4 md:h-full overflow-auto md:overflow-hidden gap-4">
      {/* Header + tab bar */}
      <div className="flex-shrink-0">
        <h2 className="text-sm font-semibold text-gray-200 uppercase tracking-wider">Integrations</h2>
        <div className="flex gap-1 mt-3 border-b border-gray-800 pb-0">
          {(['zapier', 'marketplaces'] as Tab[]).map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-2 text-xs font-medium rounded-t transition-colors capitalize ${
                tab === t
                  ? 'bg-gray-800 text-white border border-gray-700 border-b-gray-800 -mb-px'
                  : 'text-gray-500 hover:text-gray-300'
              }`}
            >
              {t === 'zapier' ? 'Zapier Webhooks' : 'Buyer Marketplaces'}
            </button>
          ))}
        </div>
      </div>

      {/* Tab content */}
      <div className="flex-1 min-h-0 overflow-auto">
        {tab === 'zapier'       && <ZapierSection />}
        {tab === 'marketplaces' && <MarketplacesSection />}
      </div>
    </div>
  );
}
