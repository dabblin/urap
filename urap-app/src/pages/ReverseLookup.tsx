import { useState } from 'react';

import { ENGINE, TENANT, API_KEY } from '../lib/config.js';

interface Identity {
  name: string;
  source: string;
  confidence: 'high' | 'medium' | 'low' | 'none';
  note?: string;
}

interface SourceStatus {
  status: string;
  reason?: string;
  errors?: { table: string; reason: string }[];
}

interface LookupResult {
  input: string;
  e164?: string;
  national?: string;
  valid: boolean;
  error?: string;
  identity?: Identity;
  line?: { carrier: string; type: string; caller_type: string };
  location?: { region: string; country_code: number; timezones: string[] };
  internal_matches?: Record<string, unknown>[];
  voice_calls?: Record<string, string>[];
  sources?: Record<string, SourceStatus>;
  web?: { summary?: string; found?: boolean; sources?: string[] };
}

const CONFIDENCE_STYLE: Record<string, string> = {
  high:   'bg-green-500/15 text-green-300 border-green-500/30',
  medium: 'bg-yellow-500/15 text-yellow-300 border-yellow-500/30',
  low:    'bg-orange-500/15 text-orange-300 border-orange-500/30',
  none:   'bg-gray-500/15 text-gray-400 border-gray-500/30',
};

const SOURCE_STYLE: Record<string, string> = {
  ok:             'text-green-400',
  partial:        'text-yellow-400',
  skipped:        'text-gray-500',
  not_configured: 'text-gray-500',
  error:          'text-red-400',
};

const SOURCE_LABEL: Record<string, string> = {
  offline:        'Offline parse',
  internal:       'URAP records',
  voice_call_log: 'Voice call log',
  twilio:         'Twilio (carrier + CNAM)',
  numverify:      'Numverify (carrier)',
  web:            'Public web',
};

export function ReverseLookup() {
  const [number, setNumber] = useState('');
  const [deep, setDeep] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<LookupResult | null>(null);
  const [error, setError] = useState('');

  async function handleLookup() {
    const trimmed = number.trim();
    if (!trimmed) return;
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const res = await fetch(`${ENGINE}/lookup/phone`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': API_KEY,
          'x-tenant-id': TENANT,
        },
        body: JSON.stringify({ number: trimmed, country: 'US', deep }),
      });
      if (!res.ok) {
        setError(`Engine returned ${res.status}`);
        return;
      }
      setResult(await res.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Lookup failed');
    } finally {
      setLoading(false);
    }
  }

  const identity = result?.identity;

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <header className="mb-6">
        <h1 className="text-2xl font-semibold text-white">Reverse Lookup</h1>
        <p className="text-sm text-gray-400 mt-1">
          Identify who owns a phone number across our own records, the AI receptionist's
          call log, carrier data, and the public web.
        </p>
      </header>

      <div className="flex flex-wrap gap-3 items-center mb-4">
        <input
          value={number}
          onChange={e => setNumber(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleLookup()}
          placeholder="(917) 555-0100"
          className="flex-1 min-w-[220px] bg-gray-900 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500"
        />
        <button
          onClick={handleLookup}
          disabled={loading || !number.trim()}
          className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-medium rounded-lg px-5 py-2.5 transition"
        >
          {loading ? 'Looking up…' : 'Look up'}
        </button>
      </div>

      <label className="flex items-center gap-2 text-sm text-gray-400 mb-6 cursor-pointer">
        <input
          type="checkbox"
          checked={deep}
          onChange={e => setDeep(e.target.checked)}
          className="accent-indigo-500"
        />
        Deep search — also scan the public web (slower, uses AI credits)
      </label>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-300 rounded-lg px-4 py-3 mb-4 text-sm">
          {error}
        </div>
      )}

      {result && !result.valid && (
        <div className="bg-orange-500/10 border border-orange-500/30 text-orange-300 rounded-lg px-4 py-3 text-sm">
          <strong>Not a valid number.</strong>{' '}
          {result.error || 'No providers were queried.'}
        </div>
      )}

      {result && result.valid && (
        <div className="space-y-4">
          <section className="bg-gray-900/60 border border-gray-800 rounded-xl p-5">
            <div className="flex items-start justify-between gap-4 flex-wrap">
              <div>
                <div className="text-xs uppercase tracking-wide text-gray-500 mb-1">Identity</div>
                <div className="text-xl font-semibold text-white">
                  {identity?.name || 'Not identified'}
                </div>
                {identity?.source && (
                  <div className="text-sm text-gray-400 mt-1">via {identity.source}</div>
                )}
              </div>
              <span
                className={`text-xs font-medium px-2.5 py-1 rounded-full border ${
                  CONFIDENCE_STYLE[identity?.confidence || 'none']
                }`}
              >
                {identity?.confidence || 'none'} confidence
              </span>
            </div>
            {identity?.note && (
              <p className="text-xs text-yellow-300/80 mt-3 border-t border-gray-800 pt-3">
                ⚠ {identity.note}
              </p>
            )}
          </section>

          <section className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <Fact label="Number" value={result.national || result.e164 || ''} />
            <Fact label="Carrier" value={result.line?.carrier || '—'} />
            <Fact label="Line type" value={(result.line?.type || '—').replace(/_/g, ' ')} />
            <Fact label="Region" value={result.location?.region || '—'} />
          </section>

          {!!result.voice_calls?.length && (
            <section className="bg-gray-900/60 border border-gray-800 rounded-xl p-5">
              <h2 className="text-sm font-semibold text-white mb-3">
                Called us ({result.voice_calls.length})
              </h2>
              <div className="space-y-2">
                {result.voice_calls.map((call, i) => (
                  <div key={i} className="text-sm border-l-2 border-indigo-500/50 pl-3">
                    <div className="text-gray-300">
                      {call['caller name'] || 'Unknown'} — {call.interest || 'no stated interest'}
                    </div>
                    <div className="text-xs text-gray-500">
                      {call.timestamp} · {call.business}
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {!!result.internal_matches?.length && (
            <section className="bg-gray-900/60 border border-gray-800 rounded-xl p-5">
              <h2 className="text-sm font-semibold text-white mb-3">
                In our records ({result.internal_matches.length})
              </h2>
              <div className="space-y-2">
                {result.internal_matches.map((m, i) => (
                  <div key={i} className="text-sm border-l-2 border-gray-700 pl-3">
                    <div className="text-gray-300">
                      {String(m.name || m.contact_name || m.company_name || '—')}
                      {m.email ? ` · ${String(m.email)}` : ''}
                    </div>
                    <div className="text-xs text-gray-500">{String(m.table)}</div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {result.web?.summary && (
            <section className="bg-gray-900/60 border border-gray-800 rounded-xl p-5">
              <h2 className="text-sm font-semibold text-white mb-2">Public web</h2>
              <p className="text-sm text-gray-300 whitespace-pre-wrap">{result.web.summary}</p>
              {!!result.web.sources?.length && (
                <ul className="mt-3 space-y-1">
                  {result.web.sources.map((url, i) => (
                    <li key={i}>
                      <a
                        href={url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-xs text-indigo-400 hover:underline break-all"
                      >
                        {url}
                      </a>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          )}

          <section className="bg-gray-900/60 border border-gray-800 rounded-xl p-5">
            <h2 className="text-sm font-semibold text-white mb-3">Sources checked</h2>
            <div className="space-y-1.5">
              {Object.entries(result.sources || {}).map(([key, val]) => (
                <div key={key} className="flex items-baseline justify-between gap-4 text-sm">
                  <span className="text-gray-400">{SOURCE_LABEL[key] || key}</span>
                  <span className={`text-xs ${SOURCE_STYLE[val.status] || 'text-gray-400'}`}>
                    {val.status}
                    {val.reason ? ` — ${val.reason}` : ''}
                  </span>
                </div>
              ))}
            </div>
          </section>

          <p className="text-xs text-gray-600 leading-relaxed">
            For identifying business contacts only. These results are not a consumer
            report and must not be used for credit, insurance, employment, or housing
            decisions.
          </p>
        </div>
      )}
    </div>
  );
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-gray-900/60 border border-gray-800 rounded-lg px-3 py-2.5">
      <div className="text-[10px] uppercase tracking-wide text-gray-500">{label}</div>
      <div className="text-sm text-white mt-0.5 truncate" title={value}>{value}</div>
    </div>
  );
}
