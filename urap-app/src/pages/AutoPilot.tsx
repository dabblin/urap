import { useState, useEffect } from 'react';

const ENGINE = 'http://localhost:8080';
const TENANT = 'dev-tenant';
const API_KEY = '';

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

  useEffect(() => { fetchConfig(); fetchMarketplaces(); }, []);

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
          disabled={running || !icp.domain}
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
              <div className="flex gap-6 text-xs">
                <span className="text-gray-300">Found: <span className="text-white font-medium">{lastRun.leads_found}</span></span>
                <span className="text-gray-300">Queued: <span className="text-white font-medium">{lastRun.sequences_queued}</span></span>
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

        {/* Cloud Scheduler note */}
        <div className="rounded border border-gray-800 bg-gray-900/50 px-4 py-3 text-xs text-gray-500 space-y-1">
          <p className="text-gray-400 font-medium">Cloud Scheduler setup</p>
          <p>To run on schedule, create a Cloud Scheduler job targeting:</p>
          <p className="font-mono text-gray-400 text-xs mt-1">POST {ENGINE}/autopilot/run</p>
          <p className="mt-1">Headers: x-api-key + x-tenant-id. Cron: <span className="font-mono">0 */24 * * *</span> for daily.</p>
        </div>

        {loading && <p className="text-gray-600 text-sm">Loading config…</p>}
      </div>
    </div>
  );
}
