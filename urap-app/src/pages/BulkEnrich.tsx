import { useState, useEffect } from 'react';

const ENGINE = 'http://localhost:8080';
const TENANT = 'dev-tenant';
const API_KEY = '';

type JobMode = 'csv' | 'icp';

interface BulkJob {
  id: string;
  source: string;
  total: number;
  enriched: number;
  failed: number;
  status: string;
  created_at: string;
}

interface BulkJobDetail extends BulkJob {
  results: Record<string, string>[];
  error: string;
}

const CSV_PLACEHOLDER = `first_name,last_name,email,company
Jane,Smith,jane@stripe.com,Stripe
John,Doe,,salesforce.com`;

function headers() {
  return { 'Content-Type': 'application/json', 'x-api-key': API_KEY, 'x-tenant-id': TENANT };
}

export function BulkEnrich() {
  const [mode, setMode] = useState<JobMode>('icp');
  const [domain, setDomain] = useState('');
  const [csvText, setCsvText] = useState('');
  const [limit, setLimit] = useState(50);
  const [running, setRunning] = useState(false);
  const [jobs, setJobs] = useState<BulkJob[]>([]);
  const [selected, setSelected] = useState<BulkJobDetail | null>(null);
  const [loadingJobs, setLoadingJobs] = useState(true);

  useEffect(() => { fetchJobs(); }, []);

  async function fetchJobs() {
    setLoadingJobs(true);
    try {
      const res = await fetch(`${ENGINE}/enrich/bulk-jobs`, { headers: headers() });
      const data = await res.json();
      setJobs(data.jobs || []);
    } catch {/* silent */} finally {
      setLoadingJobs(false);
    }
  }

  async function handleRun() {
    if (mode === 'icp' && !domain.trim()) return;
    if (mode === 'csv' && !csvText.trim()) return;
    setRunning(true);
    setSelected(null);
    try {
      const endpoint = mode === 'csv' ? '/enrich/bulk-job/csv' : '/enrich/bulk-job/icp';
      const body = mode === 'csv'
        ? { csv_text: csvText, limit }
        : { domain: domain.trim(), limit };
      const res = await fetch(`${ENGINE}${endpoint}`, {
        method: 'POST',
        headers: headers(),
        body: JSON.stringify(body),
      });
      const data: BulkJobDetail = await res.json();
      setSelected(data);
      await fetchJobs();
    } catch (err) {
      console.error('[bulk_enrich] run error', err);
    } finally {
      setRunning(false);
    }
  }

  async function loadJob(id: string) {
    try {
      const res = await fetch(`${ENGINE}/enrich/bulk-job/${id}`, { headers: headers() });
      const data: BulkJobDetail = await res.json();
      setSelected(data);
    } catch {/* silent */}
  }

  const statusColor: Record<string, string> = {
    complete: 'text-green-400',
    running: 'text-yellow-400',
    error: 'text-red-400',
  };

  return (
    <div className="flex gap-4 h-full p-4 overflow-hidden">
      {/* Left panel */}
      <div className="w-80 flex-shrink-0 flex flex-col gap-3 overflow-auto">
        <div>
          <h2 className="text-sm font-semibold text-gray-200 uppercase tracking-wider">Bulk Credits</h2>
          <p className="text-xs text-gray-500 mt-1">Large-scale enrichment from CSV or ICP domain filter.</p>
        </div>

        {/* Mode toggle */}
        <div className="flex rounded border border-gray-700 overflow-hidden text-xs">
          {(['icp', 'csv'] as JobMode[]).map(m => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`flex-1 py-2 font-medium transition-colors ${mode === m ? 'bg-gray-700 text-white' : 'bg-gray-900 text-gray-500 hover:text-gray-300'}`}
            >
              {m === 'icp' ? 'Domain / ICP' : 'CSV Upload'}
            </button>
          ))}
        </div>

        {mode === 'icp' ? (
          <input
            className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500"
            placeholder="Domain *  (e.g. stripe.com)"
            value={domain}
            onChange={e => setDomain(e.target.value)}
          />
        ) : (
          <textarea
            className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500 resize-none font-mono text-xs"
            rows={8}
            placeholder={CSV_PLACEHOLDER}
            value={csvText}
            onChange={e => setCsvText(e.target.value)}
          />
        )}

        <div className="flex items-center gap-2">
          <label className="text-xs text-gray-400 w-16 flex-shrink-0">Limit</label>
          <input
            type="number"
            min={1}
            max={200}
            className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white w-full focus:outline-none focus:border-emerald-500"
            value={limit}
            onChange={e => setLimit(parseInt(e.target.value, 10) || 50)}
          />
        </div>

        <button
          onClick={handleRun}
          disabled={running || (mode === 'icp' ? !domain.trim() : !csvText.trim())}
          className="bg-emerald-700 hover:bg-emerald-600 disabled:opacity-40 text-white text-sm font-medium rounded px-4 py-2 transition-colors"
        >
          {running ? '⚙ Running…' : '⚡ Run Bulk Enrich'}
        </button>

        <div className="text-xs text-gray-600 space-y-1">
          <p>Source: Prospeo → Snov.io waterfall</p>
          <p>Results cached in urap_contacts</p>
        </div>
      </div>

      {/* Results + job history */}
      <div className="flex-1 flex flex-col gap-3 overflow-auto">
        {/* Active result */}
        {selected && (
          <div className="rounded border border-gray-700 bg-gray-900 text-sm">
            <div className="flex justify-between items-center px-4 py-3 border-b border-gray-800">
              <div className="flex gap-4 text-xs">
                <span className="text-gray-300">Total: <span className="text-white font-medium">{selected.total}</span></span>
                <span className="text-gray-300">Enriched: <span className="text-green-400 font-medium">{selected.enriched}</span></span>
                <span className="text-gray-300">Failed: <span className="text-red-400 font-medium">{selected.failed}</span></span>
              </div>
              <span className={`text-xs font-medium ${statusColor[selected.status] || 'text-gray-400'}`}>{selected.status}</span>
            </div>
            {selected.error && (
              <p className="px-4 py-2 text-red-400 text-xs">{selected.error}</p>
            )}
            <div className="overflow-auto max-h-64">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-gray-500 border-b border-gray-800">
                    <th className="text-left px-4 py-2">Name</th>
                    <th className="text-left px-4 py-2">Email</th>
                    <th className="text-left px-4 py-2">Company</th>
                    <th className="text-left px-4 py-2">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {selected.results.slice(0, 100).map((row, i) => (
                    <tr key={i} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                      <td className="px-4 py-1.5 text-gray-300">{row.first_name || row.name || '—'} {row.last_name || ''}</td>
                      <td className="px-4 py-1.5 text-gray-400 font-mono">{row.email || '—'}</td>
                      <td className="px-4 py-1.5 text-gray-400">{row.company || '—'}</td>
                      <td className="px-4 py-1.5">
                        <span className={`px-1.5 py-0.5 rounded text-xs ${
                          row._status === 'enriched' ? 'bg-green-900/50 text-green-400' :
                          row._status === 'partial' ? 'bg-yellow-900/50 text-yellow-400' :
                          'bg-red-900/50 text-red-400'
                        }`}>{row._status}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {selected.results.length > 100 && (
                <p className="text-gray-600 text-xs px-4 py-2">Showing 100 of {selected.results.length} rows</p>
              )}
            </div>
          </div>
        )}

        {/* Job history */}
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-gray-200 uppercase tracking-wider">Job History</h2>
          <button onClick={fetchJobs} className="text-xs text-gray-500 hover:text-gray-300">↻</button>
        </div>

        {loadingJobs && <p className="text-gray-600 text-sm">Loading…</p>}
        {!loadingJobs && jobs.length === 0 && <p className="text-gray-600 text-sm">No bulk jobs yet.</p>}

        {jobs.map(job => (
          <div
            key={job.id}
            onClick={() => loadJob(job.id)}
            className="rounded border border-gray-800 bg-gray-900 px-4 py-3 text-xs cursor-pointer hover:bg-gray-800 transition-colors"
          >
            <div className="flex justify-between items-center">
              <div className="flex gap-4">
                <span className="text-gray-400 bg-gray-800 px-2 py-0.5 rounded">{job.source}</span>
                <span className="text-gray-300">Total: <span className="text-white">{job.total}</span></span>
                <span className="text-gray-300">Enriched: <span className="text-green-400">{job.enriched}</span></span>
              </div>
              <div className="flex items-center gap-2">
                <span className={statusColor[job.status] || 'text-gray-400'}>{job.status}</span>
                <span className="text-gray-600">{new Date(job.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
