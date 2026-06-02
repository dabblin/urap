import { useState, useEffect } from 'react';

import { ENGINE, TENANT } from '../lib/config.js';
const API_KEY = '';
const TCPA_KEY = 'urap_tcpa_ack_v1';

function headers() {
  return { 'Content-Type': 'application/json', 'x-api-key': API_KEY, 'x-tenant-id': TENANT };
}

interface ScoredContact {
  id: string;
  email?: string;
  first_name?: string;
  last_name?: string;
  company?: string;
  title?: string;
  industry?: string;
  global_status?: string;
  score: number;
  routed_at?: string;
}

interface Marketplace {
  id: string;
  name: string;
  cpl_range: string;
  best_for: string;
  webhook_url: string;
  cpl: number;
  configured: boolean;
}

interface RoutingSession {
  id: string;
  marketplace_name: string;
  leads_routed: number;
  estimated_earnings: number;
  failed: number;
  created_at: string;
}

interface DispatchResult {
  leads_routed: number;
  estimated_earnings: number;
  marketplace_name?: string;
  error?: string;
}

function scoreBadge(score: number) {
  if (score >= 80) return 'bg-emerald-900 text-emerald-300';
  if (score >= 60) return 'bg-yellow-900 text-yellow-300';
  if (score >= 40) return 'bg-orange-900 text-orange-300';
  return 'bg-red-900 text-red-400';
}

export function LeadRouter() {
  const [contacts, setContacts] = useState<ScoredContact[]>([]);
  const [marketplaces, setMarketplaces] = useState<Marketplace[]>([]);
  const [sessions, setSessions] = useState<RoutingSession[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [minScore, setMinScore] = useState(60);
  const [filterEmail, setFilterEmail] = useState(true);
  const [hideRouted, setHideRouted] = useState(true);
  const [pingPost, setPingPost] = useState(false);
  const [targetMarket, setTargetMarket] = useState('');
  const [tcpaAck, setTcpaAck] = useState(() => !!localStorage.getItem(TCPA_KEY));
  const [showTcpa, setShowTcpa] = useState(false);
  const [loading, setLoading] = useState(true);
  const [routing, setRouting] = useState(false);
  const [lastResult, setLastResult] = useState<DispatchResult | null>(null);

  useEffect(() => {
    fetchAll();
    if (!localStorage.getItem(TCPA_KEY)) setShowTcpa(true);
  }, []);

  async function fetchAll() {
    setLoading(true);
    await Promise.all([fetchContacts(), fetchMarketplaces(), fetchSessions()]);
    setLoading(false);
  }

  async function fetchContacts() {
    try {
      const res = await fetch(`${ENGINE}/outreach/intent/score`, {
        method: 'POST',
        headers: headers(),
        body: JSON.stringify({ limit: 200 }),
      });
      const data = await res.json();
      setContacts(data.contacts || []);
    } catch (err) {
      console.error('[lead-router] contacts error', err);
    }
  }

  async function fetchMarketplaces() {
    try {
      const res = await fetch(`${ENGINE}/route/marketplaces`, { headers: headers() });
      const data = await res.json();
      setMarketplaces(data.marketplaces || []);
    } catch (err) {
      console.error('[lead-router] marketplaces error', err);
    }
  }

  async function fetchSessions() {
    try {
      const res = await fetch(`${ENGINE}/route/sessions`, { headers: headers() });
      const data = await res.json();
      setSessions(data.sessions || []);
    } catch (err) {
      console.error('[lead-router] sessions error', err);
    }
  }

  function acknowledgeTcpa() {
    localStorage.setItem(TCPA_KEY, '1');
    setTcpaAck(true);
    setShowTcpa(false);
  }

  const filtered = contacts.filter(c => {
    if (c.score < minScore) return false;
    if (filterEmail && !c.email) return false;
    if (hideRouted && c.routed_at) return false;
    return true;
  });

  function toggleSelect(id: string) {
    setSelected(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  function toggleSelectAll() {
    if (selected.size === filtered.length && filtered.length > 0) {
      setSelected(new Set());
    } else {
      setSelected(new Set(filtered.map(c => c.id)));
    }
  }

  async function handleRoute() {
    if (!tcpaAck) { setShowTcpa(true); return; }
    if (selected.size === 0 || (!pingPost && !targetMarket)) return;
    setRouting(true);
    setLastResult(null);
    try {
      const selectedLeads = contacts.filter(c => selected.has(c.id));
      const res = await fetch(`${ENGINE}/route/dispatch`, {
        method: 'POST',
        headers: headers(),
        body: JSON.stringify({
          marketplace_id: targetMarket,
          leads: selectedLeads,
          ping_post: pingPost,
        }),
      });
      const data: DispatchResult = await res.json();
      setLastResult(data);
      setSelected(new Set());
      await fetchAll();
    } catch {
      setLastResult({ leads_routed: 0, estimated_earnings: 0, error: 'Network error — engine may be offline' });
    } finally {
      setRouting(false);
    }
  }

  const configuredMarkets = marketplaces.filter(m => m.configured);
  const totalEarned = sessions.reduce((sum, s) => sum + (s.estimated_earnings || 0), 0);
  const canRoute = tcpaAck && selected.size > 0 && (pingPost ? configuredMarkets.length > 0 : !!targetMarket) && !routing;

  return (
    <div className="flex flex-col md:flex-row gap-4 p-4 md:h-full overflow-auto md:overflow-hidden">

      {/* TCPA Compliance Modal */}
      {showTcpa && (
        <div className="fixed inset-0 bg-black/75 z-50 flex items-center justify-center p-4">
          <div className="bg-gray-900 border border-gray-700 rounded-xl max-w-md w-full p-6 space-y-4">
            <p className="text-xs text-emerald-400 font-medium uppercase tracking-wider">TCPA + CAN-SPAM Compliance Required</p>
            <h3 className="text-white font-semibold">Before routing leads to buyers</h3>
            <p className="text-gray-400 text-xs leading-relaxed">
              By routing leads to buyer marketplaces, you confirm that all contacts have provided verifiable
              consent under TCPA and CAN-SPAM requirements. Leads without valid consent must not be routed
              to phone or email buyers.
            </p>
            <p className="text-gray-500 text-xs">
              You are responsible for maintaining consent records for all leads you route. URAP logs every
              routing session for audit purposes.
            </p>
            <button
              onClick={acknowledgeTcpa}
              className="w-full bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium rounded px-4 py-2.5 transition-colors"
            >
              I confirm compliance — enable routing
            </button>
            <button
              onClick={() => setShowTcpa(false)}
              className="w-full text-gray-500 hover:text-gray-300 text-xs transition-colors py-1"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Left sidebar — filters + route controls */}
      <div className="w-full md:w-80 md:flex-shrink-0 flex flex-col gap-3 md:overflow-auto">
        <div>
          <h2 className="text-sm font-semibold text-gray-200 uppercase tracking-wider">Lead Router</h2>
          <p className="text-xs text-gray-500 mt-1">
            Route enriched contacts to buyer marketplaces. $20–$500 per qualified lead.
          </p>
        </div>

        {/* TCPA status badge */}
        <div
          onClick={() => !tcpaAck && setShowTcpa(true)}
          className={`flex items-center gap-2 px-3 py-2 rounded border text-xs transition-colors ${
            tcpaAck
              ? 'border-emerald-800 bg-emerald-950/30 text-emerald-400 cursor-default'
              : 'border-yellow-800 bg-yellow-950/20 text-yellow-400 hover:border-yellow-600 cursor-pointer'
          }`}
        >
          <span className="flex-shrink-0">{tcpaAck ? '✓' : '⚠'}</span>
          <span>{tcpaAck ? 'TCPA compliance acknowledged' : 'TCPA acknowledgment required — click to confirm'}</span>
        </div>

        {/* Filters */}
        <div className="rounded border border-gray-800 bg-gray-900 px-4 py-3 space-y-3">
          <p className="text-xs text-gray-400 font-medium uppercase tracking-wider">Filters</p>

          <div>
            <div className="flex justify-between text-xs text-gray-400 mb-1">
              <span>Min Score</span>
              <span className={`font-medium ${minScore >= 80 ? 'text-emerald-400' : minScore >= 60 ? 'text-yellow-400' : 'text-orange-400'}`}>
                {minScore}+
              </span>
            </div>
            <input
              type="range" min={0} max={100} step={5}
              value={minScore}
              onChange={e => { setMinScore(parseInt(e.target.value, 10)); setSelected(new Set()); }}
              className="w-full accent-emerald-500"
            />
          </div>

          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-400">Has Email</span>
            <button
              onClick={() => { setFilterEmail(v => !v); setSelected(new Set()); }}
              className={`w-9 h-5 rounded-full relative transition-colors ${filterEmail ? 'bg-emerald-600' : 'bg-gray-700'}`}
            >
              <span className={`block w-4 h-4 bg-white rounded-full absolute top-0.5 transition-transform ${filterEmail ? 'translate-x-4' : 'translate-x-0.5'}`} />
            </button>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-400">Hide Routed</span>
            <button
              onClick={() => { setHideRouted(v => !v); setSelected(new Set()); }}
              className={`w-9 h-5 rounded-full relative transition-colors ${hideRouted ? 'bg-emerald-600' : 'bg-gray-700'}`}
            >
              <span className={`block w-4 h-4 bg-white rounded-full absolute top-0.5 transition-transform ${hideRouted ? 'translate-x-4' : 'translate-x-0.5'}`} />
            </button>
          </div>

          <p className="text-xs text-gray-600">
            {filtered.length} in queue · {selected.size} selected
          </p>
        </div>

        {/* Route controls */}
        <div className="rounded border border-gray-800 bg-gray-900 px-4 py-3 space-y-3">
          <p className="text-xs text-gray-400 font-medium uppercase tracking-wider">Route To</p>

          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-300 font-medium">Ping/Post Mode</p>
              <p className="text-xs text-gray-600">Send to all {configuredMarkets.length} configured markets</p>
            </div>
            <button
              onClick={() => setPingPost(v => !v)}
              className={`w-9 h-5 rounded-full relative transition-colors flex-shrink-0 ml-2 ${pingPost ? 'bg-emerald-600' : 'bg-gray-700'}`}
            >
              <span className={`block w-4 h-4 bg-white rounded-full absolute top-0.5 transition-transform ${pingPost ? 'translate-x-4' : 'translate-x-0.5'}`} />
            </button>
          </div>

          {!pingPost && (
            <select
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
              value={targetMarket}
              onChange={e => setTargetMarket(e.target.value)}
            >
              <option value="">— Select marketplace —</option>
              {configuredMarkets.map(m => (
                <option key={m.id} value={m.id}>
                  {m.name}  ·  {m.cpl_range}
                </option>
              ))}
            </select>
          )}

          {configuredMarkets.length === 0 && (
            <p className="text-xs text-yellow-500">
              No marketplaces configured. Add webhook URLs in Integrations → Marketplaces.
            </p>
          )}

          <button
            onClick={handleRoute}
            disabled={!canRoute}
            className="w-full bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 text-white text-sm font-medium rounded px-4 py-2 transition-colors"
          >
            {routing
              ? '⚡ Routing…'
              : `Route${selected.size > 0 ? ` ${selected.size}` : ''} Selected`}
          </button>
        </div>

        {/* Last dispatch result */}
        {lastResult && (
          <div className={`rounded border px-4 py-3 text-sm ${lastResult.error ? 'border-red-800 bg-red-950/20' : 'border-emerald-800 bg-emerald-950/20'}`}>
            {lastResult.error ? (
              <p className="text-red-400 text-xs">{lastResult.error}</p>
            ) : (
              <div className="space-y-1.5">
                <p className="text-emerald-400 text-xs font-medium">✓ Routed successfully</p>
                <div className="flex gap-4 text-xs">
                  <span className="text-gray-300">
                    Leads: <span className="text-white font-medium">{lastResult.leads_routed}</span>
                  </span>
                  <span className="text-gray-300">
                    Est. Earnings: <span className="text-emerald-300 font-medium">
                      ${(lastResult.estimated_earnings || 0).toFixed(2)}
                    </span>
                  </span>
                </div>
                {lastResult.marketplace_name && (
                  <p className="text-gray-600 text-xs">{lastResult.marketplace_name}</p>
                )}
              </div>
            )}
          </div>
        )}

        {/* All-time session total */}
        {totalEarned > 0 && (
          <div className="rounded border border-gray-800 bg-gray-900 px-4 py-3">
            <p className="text-xs text-gray-500 uppercase tracking-wider">Est. Total Earned</p>
            <p className="text-2xl font-semibold text-emerald-400 mt-1">
              ${totalEarned.toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </p>
            <p className="text-xs text-gray-600">{sessions.length} session{sessions.length !== 1 ? 's' : ''}</p>
          </div>
        )}
      </div>

      {/* Right panel — lead queue + session log */}
      <div className="flex-1 flex flex-col gap-3 min-h-0 overflow-hidden">

        {/* Lead queue header */}
        <div className="flex items-center justify-between flex-shrink-0">
          <h2 className="text-sm font-semibold text-gray-200 uppercase tracking-wider">
            Lead Queue
            <span className="text-gray-600 font-normal ml-2 normal-case text-xs">
              ({filtered.length})
            </span>
          </h2>
          <div className="flex gap-3 items-center">
            <button onClick={toggleSelectAll} className="text-xs text-gray-500 hover:text-gray-300 transition-colors">
              {selected.size === filtered.length && filtered.length > 0 ? 'Deselect all' : 'Select all'}
            </button>
            <button onClick={fetchAll} className="text-xs text-gray-500 hover:text-gray-300 transition-colors">↻ refresh</button>
          </div>
        </div>

        {loading && <p className="text-gray-600 text-sm">Loading contacts…</p>}

        {!loading && filtered.length === 0 && (
          <p className="text-gray-600 text-sm mt-2">
            No contacts match the current filters. Lower the min score or run Prospector to add leads.
          </p>
        )}

        {/* Lead rows */}
        <div className="flex-1 overflow-auto space-y-1 min-h-0">
          {filtered.map(c => {
            const isSelected = selected.has(c.id);
            const displayName = [c.first_name, c.last_name].filter(Boolean).join(' ') || c.email || c.id;
            return (
              <div
                key={c.id}
                onClick={() => toggleSelect(c.id)}
                className={`flex items-center gap-3 px-3 py-2.5 rounded border cursor-pointer transition-colors ${
                  isSelected
                    ? 'border-emerald-700 bg-emerald-950/30'
                    : 'border-gray-800 bg-gray-900 hover:border-gray-700'
                }`}
              >
                {/* Checkbox */}
                <div
                  className={`w-4 h-4 rounded flex items-center justify-center flex-shrink-0 border transition-colors ${
                    isSelected ? 'bg-emerald-600 border-emerald-600' : 'border-gray-600'
                  }`}
                >
                  {isSelected && <span className="text-white text-[9px] font-bold">✓</span>}
                </div>

                {/* Score badge */}
                <span className={`text-xs px-1.5 py-0.5 rounded font-semibold flex-shrink-0 ${scoreBadge(c.score)}`}>
                  {c.score}
                </span>

                {/* Lead info */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white truncate">{displayName}</p>
                  <p className="text-xs text-gray-500 truncate">
                    {c.company || '—'} · {c.email || 'no email'}
                  </p>
                </div>

                {c.industry && (
                  <span className="text-xs text-gray-600 flex-shrink-0 hidden lg:block">{c.industry}</span>
                )}
                {c.routed_at && (
                  <span className="text-xs text-gray-600 flex-shrink-0 bg-gray-800 px-1.5 py-0.5 rounded">routed</span>
                )}
              </div>
            );
          })}
        </div>

        {/* Routing session log */}
        {sessions.length > 0 && (
          <div className="flex-shrink-0 border-t border-gray-800 pt-3">
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
              Routing Sessions
            </h3>
            <div className="space-y-1 max-h-44 overflow-auto">
              {sessions.map(s => (
                <div
                  key={s.id}
                  className="flex items-center gap-3 px-3 py-2 rounded border border-gray-800 bg-gray-900 text-xs"
                >
                  <span className="text-emerald-400 font-semibold flex-shrink-0 w-16">
                    ${(s.estimated_earnings || 0).toFixed(2)}
                  </span>
                  <span className="text-gray-300 flex-1 truncate">{s.marketplace_name}</span>
                  <span className="text-gray-500 flex-shrink-0">{s.leads_routed} leads</span>
                  {s.failed > 0 && (
                    <span className="text-red-500 flex-shrink-0">{s.failed} failed</span>
                  )}
                  <span className="text-gray-600 flex-shrink-0">
                    {new Date(s.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
