import { useState, useEffect } from 'react';

import { ENGINE, TENANT, API_KEY } from '../lib/config.js';

interface AutopilotConfig {
  enabled: boolean;
  icp: Record<string, unknown>;
  schedule_hours: number;
  route_after_warp?: boolean;
  route_marketplace_id?: string;
  route_min_score?: number;
  last_run_at?: string;
  last_run_stats?: {
    leads_found: number;
    sequences_queued: number;
    skipped_deduped: number;
    paused: boolean;
    pause_reason: string;
  };
}

interface MarketplaceOption {
  id: string;
  name: string;
  cpl_range: string;
  configured: boolean;
}

interface RunResult {
  job_id: string;
  leads_found: number;
  sequences_queued: number;
  skipped_deduped: number;
  paused: boolean;
  pause_reason: string;
  error: string;
  emails_sent?: number;
  emails_failed?: number;
  campaign_id?: string;
}

interface AutopilotSend {
  id: string;
  campaign_name: string;
  sent_at: string;
  name: string;
  company: string;
  title: string;
  to_email: string;
  subject: string;
  status: string;
  provider: string;
  error: string;
  body_html?: string;
}

const DEFAULT_ICP = {
  domain: '',
  title: '',
  industry: '',
  value_prop: 'AI-powered revenue acceleration that cuts SDR overhead by 60%',
  icp_label: 'Autopilot ICP',
  limit: 25,
};

const DEFAULT_ROUTE = {
  route_after_warp: false,
  route_marketplace_id: '',
  route_min_score: 60,
};

function headers() {
  return { 'Content-Type': 'application/json', 'x-api-key': API_KEY, 'x-tenant-id': TENANT };
}

export function AutoPilot() {
  const [config, setConfig] = useState<AutopilotConfig | null>(null);
  const [icp, setIcp] = useState(DEFAULT_ICP);
  const [scheduleHours, setScheduleHours] = useState(24);
  const [routeConfig, setRouteConfig] = useState(DEFAULT_ROUTE);
  const [marketplaces, setMarketplaces] = useState<MarketplaceOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState(false);
  const [running, setRunning] = useState(false);
  const [lastRun, setLastRun] = useState<RunResult | null>(null);
  const [sends, setSends] = useState<AutopilotSend[]>([]);
  const [selectedSend, setSelectedSend] = useState<AutopilotSend | null>(null);

  useEffect(() => { fetchConfig(); fetchMarketplaces(); fetchSends(); }, []);

  async function fetchSends() {
    try {
      const res = await fetch(`${ENGINE}/autopilot/sends?limit=200`, { headers: headers() });
      const data = await res.json();
      setSends(data.sends || []);
    } catch {/* silent */}
  }

  async function fetchConfig() {
    setLoading(true);
    try {
      const res = await fetch(`${ENGINE}/autopilot/config`, { headers: headers() });
      const data: AutopilotConfig = await res.json();
      setConfig(data);
      if (data.icp && Object.keys(data.icp).length) {
        setIcp({ ...DEFAULT_ICP, ...(data.icp as typeof DEFAULT_ICP) });
      }
      if (data.schedule_hours) setScheduleHours(data.schedule_hours);
      setRouteConfig({
        route_after_warp:    data.route_after_warp    ?? false,
        route_marketplace_id: data.route_marketplace_id ?? '',
        route_min_score:     data.route_min_score     ?? 60,
      });
    } catch {/* silent */} finally {
      setLoading(false);
    }
  }

  async function handleToggle() {
    if (!config) return;
    setToggling(true);
    try {
      if (config.enabled) {
        await fetch(`${ENGINE}/autopilot/disable`, { method: 'POST', headers: headers() });
        setConfig(c => c ? { ...c, enabled: false } : c);
      } else {
        const res = await fetch(`${ENGINE}/autopilot/enable`, {
          method: 'POST',
          headers: headers(),
          body: JSON.stringify({
            icp,
            schedule_hours: scheduleHours,
            route_after_warp:    routeConfig.route_after_warp,
            route_marketplace_id: routeConfig.route_marketplace_id || null,
            route_min_score:     routeConfig.route_min_score,
          }),
        });
        const data = await res.json();
        if (data.success) setConfig(c => c ? { ...c, enabled: true, icp, schedule_hours: scheduleHours } : c);
      }
    } catch {/* silent */} finally {
      setToggling(false);
    }
  }

  async function fetchMarketplaces() {
    try {
      const res = await fetch(`${ENGINE}/route/marketplaces`, { headers: headers() });
      const data = await res.json();
      setMarketplaces((data.marketplaces || []).filter((m: MarketplaceOption) => m.configured));
    } catch {/* silent */}
  }

  async function handleRunNow() {
    setRunning(true);
    setLastRun(null);
    try {
      const res = await fetch(`${ENGINE}/autopilot/run`, { method: 'POST', headers: headers() });
      const data: RunResult = await res.json();
      setLastRun(data);
      await fetchConfig();
      await fetchSends();
    } catch {/* silent */} finally {
      setRunning(false);
    }
  }

  const enabled = config?.enabled ?? false;

  return (
    <div className="flex flex-col md:flex-row gap-4 p-4 md:h-full overflow-auto md:overflow-hidden">
      {/* Config panel */}
      <div className="w-full md:w-80 md:flex-shrink-0 flex flex-col gap-3 md:overflow-auto">
        <div>
          <h2 className="text-sm font-semibold text-gray-200 uppercase tracking-wider">Autopilot</h2>
          <p className="text-xs text-gray-500 mt-1">
            Set your ICP once — Warp Mode runs on schedule, dedupes, throttles, and auto-pauses.
          </p>
        </div>

        {/* Enable / disable toggle */}
        {!loading && (
          <div className={`flex items-center gap-4 rounded border ${enabled ? 'border-purple-800 bg-purple-950/20' : 'border-gray-800 bg-gray-900'} px-5 py-4 transition-colors`}>
            <button
              onClick={handleToggle}
              disabled={toggling}
              className={`w-12 h-6 rounded-full transition-colors relative flex-shrink-0 ${enabled ? 'bg-purple-600' : 'bg-gray-700'} disabled:opacity-60`}
            >
              <span className={`block w-5 h-5 bg-white rounded-full absolute top-0.5 transition-transform ${enabled ? 'translate-x-6' : 'translate-x-0.5'}`} />
            </button>
            <div>
              <p className="text-sm text-white font-medium">{toggling ? '…' : enabled ? 'Autopilot ON' : 'Autopilot OFF'}</p>
              <p className="text-xs text-gray-500">
                {enabled
                  ? `Running every ${config?.schedule_hours ?? 24}h`
                  : 'Configure ICP below, then enable.'}
              </p>
            </div>
          </div>
        )}

        {/* ICP config */}
        <div className="rounded border border-gray-800 bg-gray-900 px-4 py-3 space-y-2">
          <p className="text-xs text-gray-400 font-medium uppercase tracking-wider mb-1">ICP Config</p>
          {(icp as any).sectors?.length > 0 && (
             <div className="text-xs text-emerald-400 mb-2 font-medium">
               Multi-Sector Outreach Active: {(icp as any).sectors.join(', ')}
             </div>
          )}
          <input
            className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
            placeholder="Domain *  (e.g. stripe.com)"
            value={icp.domain}
            onChange={e => setIcp(f => ({ ...f, domain: e.target.value }))}
          />
          <input
            className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
            placeholder="Target title  (e.g. VP of Sales)"
            value={icp.title}
            onChange={e => setIcp(f => ({ ...f, title: e.target.value }))}
          />
          <input
            className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
            placeholder="Industry  (e.g. SaaS)"
            value={icp.industry}
            onChange={e => setIcp(f => ({ ...f, industry: e.target.value }))}
          />
          <div className="flex items-center gap-2">
            <label className="text-xs text-gray-400 w-24 flex-shrink-0">Schedule (h)</label>
            <input
              type="number" min={1} max={168}
              className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white w-full focus:outline-none focus:border-purple-500"
              value={scheduleHours}
              onChange={e => setScheduleHours(parseInt(e.target.value, 10) || 24)}
            />
          </div>
          <div className="flex items-center gap-2">
            <label className="text-xs text-gray-400 w-24 flex-shrink-0">Leads / run</label>
            <input
              type="number" min={1} max={100}
              className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white w-full focus:outline-none focus:border-purple-500"
              value={icp.limit}
              onChange={e => setIcp(f => ({ ...f, limit: parseInt(e.target.value, 10) || 25 }))}
            />
          </div>
        </div>

        {/* Route Config — dispatch leads to marketplace after each Warp run */}
        <div className="rounded border border-gray-800 bg-gray-900 px-4 py-3 space-y-2">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-300 font-medium">Route after Warp</p>
              <p className="text-xs text-gray-600">Dispatch qualifying leads to a buyer marketplace after each run</p>
            </div>
            <button
              onClick={() => setRouteConfig(r => ({ ...r, route_after_warp: !r.route_after_warp }))}
              className={`w-9 h-5 rounded-full relative transition-colors flex-shrink-0 ml-2 ${routeConfig.route_after_warp ? 'bg-emerald-600' : 'bg-gray-700'}`}
            >
              <span className={`block w-4 h-4 bg-white rounded-full absolute top-0.5 transition-transform ${routeConfig.route_after_warp ? 'translate-x-4' : 'translate-x-0.5'}`} />
            </button>
          </div>

          {routeConfig.route_after_warp && (
            <>
              <select
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                value={routeConfig.route_marketplace_id}
                onChange={e => setRouteConfig(r => ({ ...r, route_marketplace_id: e.target.value }))}
              >
                <option value="">— Select marketplace —</option>
                {marketplaces.map(m => (
                  <option key={m.id} value={m.id}>{m.name} · {m.cpl_range}</option>
                ))}
              </select>
              {marketplaces.length === 0 && (
                <p className="text-xs text-yellow-500">No configured marketplaces. Add webhook URLs in Integrations → Marketplaces.</p>
              )}
              <div className="flex items-center gap-2">
                <label className="text-xs text-gray-400 w-24 flex-shrink-0">Min Score</label>
                <input
                  type="number" min={0} max={100} step={5}
                  className="bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-xs text-white w-full focus:outline-none focus:border-emerald-500"
                  value={routeConfig.route_min_score}
                  onChange={e => setRouteConfig(r => ({ ...r, route_min_score: parseInt(e.target.value, 10) || 60 }))}
                />
              </div>
            </>
          )}
        </div>

        <button
          onClick={handleRunNow}
          disabled={running}
          className="bg-gray-700 hover:bg-gray-600 disabled:opacity-40 text-white text-sm font-medium rounded px-4 py-2 transition-colors"
        >
          {running ? '⚡ Running…' : '▶ Run Now'}
        </button>

        <div className="text-xs text-gray-600 space-y-1">
          <p>Dedup: skips active/replied leads</p>
          <p>Throttle: daily send limit enforced</p>
          <p>Auto-pause: &gt;5% unsubscribe rate</p>
        </div>
      </div>

      {/* Status panel */}
      <div className="flex-1 flex flex-col gap-3 overflow-auto">
        <h2 className="text-sm font-semibold text-gray-200 uppercase tracking-wider">Run Status</h2>

        {/* Last manual run result */}
        {lastRun && (
          <div className={`rounded border ${lastRun.paused ? 'border-yellow-800 bg-yellow-950/20' : lastRun.error ? 'border-red-800 bg-red-950/20' : 'border-purple-800 bg-purple-950/20'} px-4 py-3 text-sm space-y-2`}>
            <p className="text-xs font-medium text-gray-300 uppercase tracking-wider">Last Run</p>
            {lastRun.error ? (
              <p className="text-red-400 text-xs">{lastRun.error}</p>
            ) : lastRun.paused ? (
              <p className="text-yellow-400 text-xs">Paused: {lastRun.pause_reason}</p>
            ) : (
              <div className="flex flex-wrap gap-6 text-xs">
                <span className="text-gray-300">Found: <span className="text-white font-medium">{lastRun.leads_found}</span></span>
                <span className="text-gray-300">Sent: <span className="text-emerald-400 font-medium">{lastRun.emails_sent ?? 0}</span></span>
                <span className="text-gray-300">Failed: <span className={lastRun.emails_failed ? 'text-red-400' : 'text-gray-400'}>{lastRun.emails_failed ?? 0}</span></span>
                <span className="text-gray-300">Deduped: <span className="text-gray-400">{lastRun.skipped_deduped}</span></span>
              </div>
            )}
            {lastRun.job_id && <p className="text-gray-600 text-xs font-mono">Job: {lastRun.job_id.slice(0, 8)}…</p>}
          </div>
        )}

        {/* Persisted last run stats */}
        {config?.last_run_at && (
          <div className="rounded border border-gray-800 bg-gray-900 px-4 py-3 text-sm space-y-2">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Scheduled Run History</p>
            <p className="text-gray-500 text-xs">Last run: {new Date(config.last_run_at).toLocaleString()}</p>
            {config.last_run_stats && (
              <div className="flex gap-6 text-xs">
                <span className="text-gray-300">Found: <span className="text-white">{config.last_run_stats.leads_found}</span></span>
                <span className="text-gray-300">Queued: <span className="text-white">{config.last_run_stats.sequences_queued}</span></span>
                <span className="text-gray-300">Deduped: <span className="text-gray-400">{config.last_run_stats.skipped_deduped}</span></span>
                {config.last_run_stats.paused && (
                  <span className="text-yellow-400">⚠ paused: {config.last_run_stats.pause_reason}</span>
                )}
              </div>
            )}
          </div>
        )}

        {/* Send report */}
        <div className="rounded border border-gray-800 bg-gray-900 overflow-hidden">
          <div className="flex items-center justify-between px-4 py-2.5 border-b border-gray-800">
            <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">Autopilot Sends</p>
            <span className="text-xs text-gray-600">{sends.length} recent</span>
          </div>
          {sends.length === 0 ? (
            <p className="px-4 py-6 text-center text-xs text-gray-600">
              No autopilot sends yet — they appear here after each scheduled or manual run.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs" style={{ minWidth: '760px' }}>
                <thead>
                  <tr className="border-b border-gray-800 text-left text-gray-500 uppercase tracking-wider">
                    <th className="px-4 py-2 font-medium">Sent</th>
                    <th className="px-4 py-2 font-medium">Contact</th>
                    <th className="px-4 py-2 font-medium">Company</th>
                    <th className="px-4 py-2 font-medium">Email</th>
                    <th className="px-4 py-2 font-medium">Subject</th>
                    <th className="px-4 py-2 font-medium text-center">Actions</th>
                    <th className="px-4 py-2 font-medium">Status</th>
                    <th className="px-4 py-2 font-medium">Provider</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800/60">
                  {sends.map(s => (
                    <tr key={s.id} className="hover:bg-gray-800/40 transition-colors">
                      <td className="px-4 py-2 text-gray-500 font-mono whitespace-nowrap">{s.sent_at?.slice(0, 16).replace('T', ' ') || '—'}</td>
                      <td className="px-4 py-2 text-white">{s.name || '—'}</td>
                      <td className="px-4 py-2 text-gray-300">{s.company || '—'}</td>
                      <td className="px-4 py-2 text-gray-400 font-mono">{s.to_email}</td>
                      <td className="px-4 py-2 text-gray-400 max-w-[220px] truncate" title={s.subject}>{s.subject || '—'}</td>
                      <td className="px-4 py-2 text-center">
                        <button
                          onClick={() => setSelectedSend(s)}
                          className="bg-gray-800 hover:bg-gray-700 text-gray-300 text-[10px] font-medium rounded px-2 py-1 transition-colors"
                        >
                          View
                        </button>
                      </td>
                      <td className="px-4 py-2">
                        <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${s.status === 'sent' ? 'bg-emerald-950 text-emerald-400' : 'bg-red-950 text-red-400'}`} title={s.error || undefined}>
                          {s.status}
                        </span>
                      </td>
                      <td className="px-4 py-2 text-gray-500">{s.provider || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Schedule note */}
        <div className="rounded border border-gray-800 bg-gray-900/50 px-4 py-3 text-xs text-gray-500 space-y-1">
          <p className="text-gray-400 font-medium">Daily schedule</p>
          <p>Gravity Claw triggers <span className="font-mono text-gray-400">POST {ENGINE}/autopilot/run</span> every morning at 8:00 AM ET (launchd job <span className="font-mono">com.antigravity.urap-autopilot</span>).</p>
        </div>

        {loading && <p className="text-gray-600 text-sm">Loading config…</p>}
      </div>

      {/* Modal for viewing email body */}
      {selectedSend && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4">
          <div className="relative flex max-h-[85vh] w-full max-w-2xl flex-col rounded-lg border border-gray-800 bg-gray-900 shadow-xl">
            <div className="flex items-center justify-between border-b border-gray-800 px-4 py-3">
              <h3 className="text-sm font-semibold text-white">Email to {selectedSend.to_email}</h3>
              <button
                onClick={() => setSelectedSend(null)}
                className="rounded text-gray-400 hover:bg-gray-800 hover:text-white px-2 py-1"
              >
                ✕
              </button>
            </div>
            <div className="flex-1 overflow-auto p-4">
              <div className="mb-4 space-y-1 rounded border border-gray-800 bg-gray-950/50 p-3 text-xs">
                <p><span className="font-semibold text-gray-500">From:</span> URAP Engine</p>
                <p><span className="font-semibold text-gray-500">To:</span> {selectedSend.name} &lt;{selectedSend.to_email}&gt;</p>
                <p><span className="font-semibold text-gray-500">Subject:</span> {selectedSend.subject}</p>
                <p><span className="font-semibold text-gray-500">Sent At:</span> {selectedSend.sent_at}</p>
              </div>
              <div 
                className="rounded border border-gray-800 bg-white text-gray-900 p-4 text-sm"
                dangerouslySetInnerHTML={{ __html: selectedSend.body_html || '<p class="text-gray-500 italic">No content available.</p>' }} 
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
