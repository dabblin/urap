import { useState } from 'react';

const ENGINE = 'http://localhost:8080';
const TENANT = 'dev-tenant';
const API_KEY = '';

interface WarpForm {
  domain: string;
  title: string;
  industry: string;
  valueProp: string;
  icpLabel: string;
  limit: number;
}

interface WarpLead {
  lead_id: string;
  name: string;
  email: string;
  title: string;
  company: string;
  subject: string;
  body_preview: string;
  body_html: string;
  copy_status: string;
}

interface WarpResult {
  job_id: string;
  icp_label: string;
  leads_found: number;
  sequences_queued: number;
  generated: WarpLead[];
  error?: string;
}

const EMPTY_FORM: WarpForm = {
  domain: '',
  title: '',
  industry: '',
  valueProp: 'AI-powered revenue acceleration that cuts SDR overhead by 60%',
  icpLabel: '',
  limit: 10,
};

const STATUS_BADGE: Record<string, string> = {
  reviewed: 'bg-green-900 text-green-300',
  generated: 'bg-blue-900 text-blue-300',
  fallback: 'bg-yellow-900 text-yellow-300',
  error: 'bg-red-900 text-red-400',
};

export function WarpMode() {
  const [form, setForm] = useState<WarpForm>(EMPTY_FORM);
  const [result, setResult] = useState<WarpResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState<string | null>(null);

  function setField(key: keyof WarpForm, value: string | number) {
    setForm(f => ({ ...f, [key]: value }));
  }

  async function handleLaunch() {
    if (!form.domain) return;
    setLoading(true);
    setResult(null);
    try {
      const res = await fetch(`${ENGINE}/agents/warp/run`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': API_KEY,
          'x-tenant-id': TENANT,
        },
        body: JSON.stringify({
          domain: form.domain,
          title: form.title,
          industry: form.industry,
          value_prop: form.valueProp,
          icp_label: form.icpLabel || `${form.title || 'ICP'} @ ${form.domain}`,
          limit: form.limit,
        }),
      });
      const data = await res.json();
      setResult(data);
    } catch (err) {
      setResult({
        job_id: '',
        icp_label: '',
        leads_found: 0,
        sequences_queued: 0,
        generated: [],
        error: String(err),
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex gap-4 h-full p-4 overflow-hidden">
      {/* ICP form */}
      <div className="w-80 flex-shrink-0 flex flex-col gap-3 overflow-auto">
        <div>
          <h2 className="text-sm font-semibold text-gray-200 uppercase tracking-wider">Warp Mode</h2>
          <p className="text-xs text-gray-500 mt-1">ICP → Enrich → AI Copy → Queue</p>
        </div>

        <input
          className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
          placeholder="Domain to search *  (e.g. stripe.com)"
          value={form.domain}
          onChange={e => setField('domain', e.target.value)}
        />
        <input
          className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
          placeholder="Target title  (e.g. VP of Sales)"
          value={form.title}
          onChange={e => setField('title', e.target.value)}
        />
        <input
          className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
          placeholder="Industry  (e.g. SaaS, FinTech)"
          value={form.industry}
          onChange={e => setField('industry', e.target.value)}
        />
        <textarea
          className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 resize-none"
          rows={3}
          placeholder="Value prop for copy generation"
          value={form.valueProp}
          onChange={e => setField('valueProp', e.target.value)}
        />
        <input
          className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
          placeholder="Campaign label  (optional)"
          value={form.icpLabel}
          onChange={e => setField('icpLabel', e.target.value)}
        />
        <div className="flex items-center gap-2">
          <label className="text-xs text-gray-400 w-20 flex-shrink-0">Lead limit</label>
          <input
            type="number"
            min={1}
            max={25}
            className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white w-full focus:outline-none focus:border-purple-500"
            value={form.limit}
            onChange={e => setField('limit', parseInt(e.target.value, 10) || 10)}
          />
        </div>

        <button
          onClick={handleLaunch}
          disabled={loading || !form.domain}
          className="bg-purple-600 hover:bg-purple-500 disabled:opacity-40 text-white text-sm font-medium rounded px-4 py-2 transition-colors"
        >
          {loading ? '⚡ Warping…' : '⚡ Launch Warp'}
        </button>

        <div className="text-xs text-gray-600 space-y-1">
          <p>Draft: Gemini 2.0 Flash</p>
          <p>Review: Claude Sonnet 4.6</p>
          <p>Fallback: static template if keys absent</p>
        </div>
      </div>

      {/* Results */}
      <div className="flex-1 flex flex-col gap-3 overflow-auto">
        <h2 className="text-sm font-semibold text-gray-200 uppercase tracking-wider">
          Generated Sequences
        </h2>

        {!result && !loading && (
          <p className="text-gray-600 text-sm mt-4">
            Configure an ICP and launch Warp Mode to generate personalized sequences.
          </p>
        )}

        {result?.error && (
          <div className="rounded border border-red-800 bg-red-950 px-4 py-3 text-sm text-red-400">
            {result.error}
          </div>
        )}

        {result && !result.error && (
          <div className="rounded border border-purple-800 bg-purple-950/30 px-4 py-3 text-sm mb-2">
            <div className="flex gap-6">
              <span className="text-gray-300">
                Leads found: <span className="text-white font-medium">{result.leads_found}</span>
              </span>
              <span className="text-gray-300">
                Sequences queued: <span className="text-white font-medium">{result.sequences_queued}</span>
              </span>
              <span className="text-gray-500 text-xs">Job: {result.job_id?.slice(0, 8)}…</span>
            </div>
          </div>
        )}

        {result?.generated.map(lead => (
          <div
            key={lead.lead_id}
            className="rounded border border-gray-800 bg-gray-900 text-sm"
          >
            <div
              className="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-gray-800 transition-colors"
              onClick={() => setExpanded(expanded === lead.lead_id ? null : lead.lead_id)}
            >
              <div className="flex flex-col gap-0.5">
                <span className="text-white font-medium">{lead.name}</span>
                <span className="text-gray-400 text-xs">{lead.title} @ {lead.company}</span>
              </div>
              <div className="flex items-center gap-3">
                <span className={`text-xs px-2 py-0.5 rounded-full ${STATUS_BADGE[lead.copy_status] || 'bg-gray-800 text-gray-400'}`}>
                  {lead.copy_status}
                </span>
                <span className="text-gray-500 text-xs">{expanded === lead.lead_id ? '▲' : '▼'}</span>
              </div>
            </div>

            {expanded === lead.lead_id && (
              <div className="border-t border-gray-800 px-4 py-3 space-y-2">
                <div>
                  <p className="text-xs text-gray-500 mb-1">Subject</p>
                  <p className="text-gray-200">{lead.subject}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500 mb-1">Body</p>
                  <div
                    className="text-gray-300 text-xs leading-relaxed [&_p]:mb-2"
                    dangerouslySetInnerHTML={{ __html: lead.body_html }}
                  />
                </div>
                <div className="flex gap-3 pt-1">
                  <span className="text-xs text-gray-500">{lead.email}</span>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
