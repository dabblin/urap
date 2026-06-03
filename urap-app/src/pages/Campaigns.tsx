import { useState, useEffect, useCallback } from 'react';
import { ENGINE, TENANT } from '../lib/config.js';

const API_KEY = '';

const HEADERS = {
  'Content-Type': 'application/json',
  'x-api-key': API_KEY,
  'x-tenant-id': TENANT,
};

// ── Types ─────────────────────────────────────────────────────────────────────

interface CampaignList {
  id: string;
  name: string;
  contact_count: number;
  created_at: string;
}

interface Campaign {
  id: string;
  name: string;
  list_id: string;
  from_email: string;
  from_name: string;
  subject_template: string;
  ai_personalize: boolean;
  status: 'draft' | 'sending' | 'sent';
  sent_count: number;
  failed_count: number;
  created_at: string;
}

interface DispatchResult {
  sent: number;
  failed: number;
  skipped: number;
}

interface FormState {
  name: string;
  list_id: string;
  from_name: string;
  from_email: string;
  subject_template: string;
  body_template: string;
  ai_personalize: boolean;
}

const EMPTY_FORM: FormState = {
  name: '',
  list_id: '',
  from_name: '',
  from_email: '',
  subject_template: '',
  body_template: '',
  ai_personalize: false,
};

const MERGE_HINT = '{{name}}  {{first_name}}  {{company}}  {{title}}  {{personalized_opener}}';

// ── Status badge ──────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: Campaign['status'] }) {
  const styles: Record<Campaign['status'], string> = {
    draft:   'bg-gray-800 text-gray-400 border border-gray-700',
    sending: 'bg-yellow-900/60 text-yellow-300 border border-yellow-700',
    sent:    'bg-green-900/60 text-green-300 border border-green-800',
  };
  return (
    <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider ${styles[status]}`}>
      {status}
    </span>
  );
}

// ── Main ──────────────────────────────────────────────────────────────────────

export function Campaigns() {
  const [lists, setLists]               = useState<CampaignList[]>([]);
  const [campaigns, setCampaigns]       = useState<Campaign[]>([]);
  const [selected, setSelected]         = useState<Campaign | null>(null);
  const [view, setView]                 = useState<'idle' | 'builder' | 'stats'>('idle');
  const [form, setForm]                 = useState<FormState>(EMPTY_FORM);
  const [dispatching, setDispatching]   = useState(false);
  const [result, setResult]             = useState<DispatchResult | null>(null);
  const [error, setError]               = useState<string | null>(null);

  const fetchLists = useCallback(async () => {
    try {
      const res = await fetch(`${ENGINE}/campaigns/lists`, { headers: HEADERS });
      const data = await res.json();
      setLists(data.lists ?? []);
    } catch { /* silent */ }
  }, []);

  const fetchCampaigns = useCallback(async () => {
    try {
      const res = await fetch(`${ENGINE}/campaigns`, { headers: HEADERS });
      const data = await res.json();
      setCampaigns(data.campaigns ?? []);
    } catch { /* silent */ }
  }, []);

  useEffect(() => {
    fetchLists();
    fetchCampaigns();
  }, [fetchLists, fetchCampaigns]);

  function setField<K extends keyof FormState>(key: K, val: FormState[K]) {
    setForm(f => ({ ...f, [key]: val }));
  }

  async function handleCreateAndSend() {
    if (!form.name || !form.list_id || !form.from_email || !form.subject_template || !form.body_template) return;
    setDispatching(true);
    setError(null);
    setResult(null);
    try {
      // 1. Create campaign
      const createRes = await fetch(`${ENGINE}/campaigns`, {
        method: 'POST', headers: HEADERS,
        body: JSON.stringify({
          name: form.name, list_id: form.list_id,
          from_email: form.from_email, from_name: form.from_name,
          subject_template: form.subject_template, body_template: form.body_template,
          ai_personalize: form.ai_personalize,
        }),
      });
      const campaign: Campaign = await createRes.json();
      if (!campaign.id) throw new Error('Campaign creation failed');

      // 2. Dispatch
      const dispatchRes = await fetch(`${ENGINE}/campaigns/${campaign.id}/dispatch`, {
        method: 'POST', headers: HEADERS,
      });
      const dispatchData: DispatchResult = await dispatchRes.json();
      setResult(dispatchData);
      setForm(EMPTY_FORM);
      await fetchCampaigns();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setDispatching(false);
    }
  }

  const canSubmit = !dispatching && !!form.name && !!form.list_id && !!form.from_email
    && !!form.subject_template && !!form.body_template;

  const selectedList = lists.find(l => l.id === form.list_id);

  return (
    <div className="flex h-full overflow-hidden">

      {/* ── Left: campaign list ─────────────────────────────────────────────── */}
      <aside className="w-[280px] shrink-0 border-r border-gray-800 bg-gray-900 flex flex-col h-full">
        <div className="px-4 py-3 border-b border-gray-800 flex items-center justify-between shrink-0">
          <span className="text-sm font-semibold text-white">Campaigns</span>
          <button
            onClick={() => { setView('builder'); setSelected(null); setResult(null); setError(null); }}
            className="text-xs px-2.5 py-1 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg transition-colors"
          >
            + New
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          {campaigns.length === 0 ? (
            <p className="text-gray-600 text-xs px-4 py-6">No campaigns yet.</p>
          ) : (
            campaigns.map(c => (
              <button
                key={c.id}
                onClick={() => { setSelected(c); setView('stats'); }}
                className={`w-full text-left px-4 py-3 border-b border-gray-800/60 hover:bg-gray-800/50 transition-colors
                  ${selected?.id === c.id ? 'bg-gray-800' : ''}`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm text-white font-medium truncate pr-2">{c.name}</span>
                  <StatusBadge status={c.status} />
                </div>
                <div className="flex items-center gap-3 text-xs text-gray-500">
                  {c.status !== 'draft' && (
                    <>
                      <span className="text-green-400">{c.sent_count} sent</span>
                      {c.failed_count > 0 && <span className="text-red-400">{c.failed_count} failed</span>}
                    </>
                  )}
                  {c.ai_personalize && <span className="text-purple-400">AI ✦</span>}
                </div>
              </button>
            ))
          )}
        </div>
      </aside>

      {/* ── Right: builder or stats ─────────────────────────────────────────── */}
      <div className="flex-1 overflow-auto p-6">

        {/* Empty state */}
        {view === 'idle' && (
          <div className="flex flex-col items-center justify-center h-full text-center pb-16">
            <div className="text-4xl mb-4">📨</div>
            <h2 className="text-white font-semibold text-lg mb-1">Batch Email Campaigns</h2>
            <p className="text-gray-500 text-sm max-w-xs">
              Pick a saved contact list, write a template, and let Claude Haiku personalize each email.
            </p>
            <button
              onClick={() => setView('builder')}
              className="mt-6 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm rounded-lg transition-colors"
            >
              New Campaign
            </button>
          </div>
        )}

        {/* Stats view */}
        {view === 'stats' && selected && (
          <div className="max-w-xl">
            <div className="flex items-center gap-3 mb-6">
              <h2 className="text-white text-lg font-semibold">{selected.name}</h2>
              <StatusBadge status={selected.status} />
            </div>
            <div className="grid grid-cols-3 gap-4 mb-6">
              {[
                { label: 'Sent',    value: selected.sent_count,                   color: 'text-green-400' },
                { label: 'Failed',  value: selected.failed_count,                 color: 'text-red-400'   },
                { label: 'AI',      value: selected.ai_personalize ? 'On' : 'Off', color: 'text-purple-400'},
              ].map(s => (
                <div key={s.label} className="bg-gray-900 border border-gray-800 rounded-xl p-4 text-center">
                  <div className={`text-2xl font-bold ${s.color}`}>{s.value}</div>
                  <div className="text-xs text-gray-500 mt-1">{s.label}</div>
                </div>
              ))}
            </div>
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 space-y-2 text-sm">
              <div className="flex gap-2 text-gray-400"><span className="text-gray-600 w-28">From</span>{selected.from_name} &lt;{selected.from_email}&gt;</div>
              <div className="flex gap-2 text-gray-400"><span className="text-gray-600 w-28">Subject</span>{selected.subject_template}</div>
            </div>
          </div>
        )}

        {/* Campaign builder */}
        {view === 'builder' && (
          <div className="max-w-2xl space-y-5">
            <h2 className="text-white text-lg font-semibold">New Campaign</h2>

            {/* Name */}
            <div>
              <label className="block text-xs text-gray-400 mb-1.5">Campaign Name</label>
              <input
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500"
                placeholder="Q3 Outreach — Insurance Leads"
                value={form.name}
                onChange={e => setField('name', e.target.value)}
              />
            </div>

            {/* List picker */}
            <div>
              <label className="block text-xs text-gray-400 mb-1.5">Contact List</label>
              {lists.length === 0 ? (
                <div className="text-xs text-yellow-500 bg-yellow-900/20 border border-yellow-800/40 rounded-lg px-3 py-2">
                  No saved lists yet — run a Prospector search and save results first.
                </div>
              ) : (
                <select
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                  value={form.list_id}
                  onChange={e => setField('list_id', e.target.value)}
                >
                  <option value="">Select a list…</option>
                  {lists.map(l => (
                    <option key={l.id} value={l.id}>{l.name} ({l.contact_count} contacts)</option>
                  ))}
                </select>
              )}
              {selectedList && (
                <p className="text-xs text-gray-500 mt-1">{selectedList.contact_count} contacts will receive this campaign.</p>
              )}
            </div>

            {/* From */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-gray-400 mb-1.5">From Name</label>
                <input
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500"
                  placeholder="Dennis Day II"
                  value={form.from_name}
                  onChange={e => setField('from_name', e.target.value)}
                />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1.5">From Email <span className="text-red-400">*</span></label>
                <input
                  type="email"
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500"
                  placeholder="dennis@dabblin.com"
                  value={form.from_email}
                  onChange={e => setField('from_email', e.target.value)}
                />
              </div>
            </div>

            {/* Subject */}
            <div>
              <label className="block text-xs text-gray-400 mb-1.5">Subject Template <span className="text-red-400">*</span></label>
              <input
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500"
                placeholder="Quick question for {{first_name}} at {{company}}"
                value={form.subject_template}
                onChange={e => setField('subject_template', e.target.value)}
              />
            </div>

            {/* Body */}
            <div>
              <label className="block text-xs text-gray-400 mb-1.5">Body Template (HTML) <span className="text-red-400">*</span></label>
              <textarea
                rows={8}
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500 resize-none font-mono"
                placeholder={`<p>{{personalized_opener}}</p>\n<p>I'm reaching out because...</p>`}
                value={form.body_template}
                onChange={e => setField('body_template', e.target.value)}
              />
              <p className="text-[11px] text-gray-600 mt-1">Merge vars: {MERGE_HINT}</p>
            </div>

            {/* AI Personalize toggle */}
            <div className="flex items-start gap-3 p-4 bg-gray-900/60 border border-gray-800 rounded-xl">
              <button
                onClick={() => setField('ai_personalize', !form.ai_personalize)}
                className={`relative mt-0.5 w-10 h-5 rounded-full flex-shrink-0 transition-colors ${form.ai_personalize ? 'bg-purple-600' : 'bg-gray-700'}`}
              >
                <span className={`absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${form.ai_personalize ? 'translate-x-5' : 'translate-x-0.5'}`} />
              </button>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-white">AI Personalization</span>
                  <span className="text-[10px] px-1.5 py-0.5 bg-purple-900/60 text-purple-300 border border-purple-800 rounded-full font-semibold">Claude Haiku</span>
                </div>
                <p className="text-xs text-gray-500 mt-0.5">
                  Writes a unique opening sentence for each lead based on their name, title, and company.
                  Use <code className="text-purple-400">{'{{personalized_opener}}'}</code> in your body template.
                </p>
              </div>
            </div>

            {/* Error / result */}
            {error && (
              <div className="p-3 bg-red-900/30 border border-red-700/60 rounded-lg text-red-300 text-sm">{error}</div>
            )}
            {result && (
              <div className="p-4 bg-green-900/20 border border-green-800/50 rounded-xl">
                <p className="text-green-300 font-semibold text-sm mb-1">Campaign sent</p>
                <div className="flex gap-6 text-sm">
                  <span className="text-green-400">{result.sent} delivered</span>
                  {result.failed > 0 && <span className="text-red-400">{result.failed} failed</span>}
                  {result.skipped > 0 && <span className="text-gray-500">{result.skipped} skipped</span>}
                </div>
              </div>
            )}

            {/* Submit */}
            <button
              onClick={handleCreateAndSend}
              disabled={!canSubmit}
              className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white text-sm font-medium rounded-lg transition-colors"
            >
              {dispatching
                ? <span className="flex items-center justify-center gap-2"><span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />Sending campaign…</span>
                : 'Send Campaign'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
