import { useState, useEffect } from 'react';

const ENGINE = 'http://localhost:8080';
const TENANT = 'dev-tenant';
const API_KEY = '';

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

function headers() {
  return { 'Content-Type': 'application/json', 'x-api-key': API_KEY, 'x-tenant-id': TENANT };
}

export function Integrations() {
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
      console.error('[integrations] fetch error', err);
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
      console.error('[integrations] subscribe error', err);
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
      console.error('[integrations] delete error', err);
    }
  }

  return (
    <div className="flex flex-col md:flex-row gap-4 p-4 md:h-full overflow-auto md:overflow-hidden">
      {/* Subscribe form */}
      <div className="w-full md:w-80 md:flex-shrink-0 flex flex-col gap-3">
        <div>
          <h2 className="text-sm font-semibold text-gray-200 uppercase tracking-wider">Integrations</h2>
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
          <h2 className="text-sm font-semibold text-gray-200 uppercase tracking-wider">Active Webhooks</h2>
          <button onClick={fetchWebhooks} className="text-xs text-gray-500 hover:text-gray-300">↻ refresh</button>
        </div>

        {loading && <p className="text-gray-600 text-sm mt-4">Loading…</p>}

        {!loading && webhooks.length === 0 && (
          <p className="text-gray-600 text-sm mt-4">No webhooks configured yet.</p>
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
