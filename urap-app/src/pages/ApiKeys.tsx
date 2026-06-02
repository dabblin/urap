import { useState, useEffect } from 'react';

const ENGINE = 'http://localhost:8080';
const TENANT = 'dev-tenant';
const API_KEY = '';

interface ApiKeyRecord {
  id: string;
  name: string;
  key_prefix: string;
  active: boolean;
  created_at: string;
  last_used_at: string | null;
}

function headers() {
  return { 'Content-Type': 'application/json', 'x-api-key': API_KEY, 'x-tenant-id': TENANT };
}

export function ApiKeys() {
  const [keys, setKeys] = useState<ApiKeyRecord[]>([]);
  const [name, setName] = useState('');
  const [generating, setGenerating] = useState(false);
  const [newKey, setNewKey] = useState('');
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => { fetchKeys(); }, []);

  async function fetchKeys() {
    setLoading(true);
    try {
      const res = await fetch(`${ENGINE}/api/keys`, { headers: headers() });
      const data = await res.json();
      setKeys(data.keys || []);
    } catch (err) {
      console.error('[api_keys] fetch error', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleGenerate() {
    if (!name.trim()) return;
    setGenerating(true);
    setNewKey('');
    try {
      const res = await fetch(`${ENGINE}/api/keys`, {
        method: 'POST',
        headers: headers(),
        body: JSON.stringify({ name: name.trim() }),
      });
      const data = await res.json();
      if (data.key) {
        setNewKey(data.key);
        setName('');
        await fetchKeys();
      }
    } catch (err) {
      console.error('[api_keys] generate error', err);
    } finally {
      setGenerating(false);
    }
  }

  async function handleRevoke(id: string) {
    try {
      await fetch(`${ENGINE}/api/keys/${id}`, { method: 'DELETE', headers: headers() });
      setKeys(prev => prev.map(k => k.id === id ? { ...k, active: false } : k));
    } catch (err) {
      console.error('[api_keys] revoke error', err);
    }
  }

  function copyKey() {
    navigator.clipboard.writeText(newKey);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="flex flex-col md:flex-row gap-4 p-4 md:h-full overflow-auto md:overflow-hidden">
      {/* Generate panel */}
      <div className="w-full md:w-80 md:flex-shrink-0 flex flex-col gap-3">
        <div>
          <h2 className="text-sm font-semibold text-gray-200 uppercase tracking-wider">API</h2>
          <p className="text-xs text-gray-500 mt-1">
            Developer API keys for tenant-scoped REST access. Plaintext shown once.
          </p>
        </div>

        <div className="rounded border border-gray-800 bg-gray-900 px-4 py-3 space-y-3">
          <p className="text-xs text-gray-400 font-medium uppercase tracking-wider">Generate Key</p>
          <input
            className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
            placeholder="Key name *  (e.g. Production)"
            value={name}
            onChange={e => setName(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleGenerate()}
          />
          <button
            onClick={handleGenerate}
            disabled={generating || !name.trim()}
            className="w-full bg-cyan-700 hover:bg-cyan-600 disabled:opacity-40 text-white text-sm font-medium rounded px-4 py-2 transition-colors"
          >
            {generating ? 'Generating…' : '+ Generate Key'}
          </button>
        </div>

        {newKey && (
          <div className="rounded border border-cyan-800 bg-cyan-950/30 px-4 py-3 space-y-2">
            <p className="text-cyan-400 text-xs font-medium uppercase tracking-wider">
              Copy now — shown once
            </p>
            <p className="text-white text-xs font-mono break-all leading-relaxed">{newKey}</p>
            <button
              onClick={copyKey}
              className="w-full bg-cyan-800 hover:bg-cyan-700 text-white text-xs rounded px-3 py-1.5 transition-colors"
            >
              {copied ? '✓ Copied' : 'Copy to clipboard'}
            </button>
          </div>
        )}

        <div className="text-xs text-gray-600 space-y-1">
          <p>Header: x-api-key: urap_…</p>
          <p>Header: x-tenant-id: your-tenant-id</p>
          <p>Keys are SHA-256 hashed at rest</p>
        </div>
      </div>

      {/* Key list */}
      <div className="flex-1 flex flex-col gap-2 overflow-auto">
        <h2 className="text-sm font-semibold text-gray-200 uppercase tracking-wider">Active Keys</h2>

        {loading && <p className="text-gray-600 text-sm mt-4">Loading…</p>}

        {!loading && keys.length === 0 && (
          <p className="text-gray-600 text-sm mt-4">No API keys yet.</p>
        )}

        {keys.map(k => (
          <div key={k.id} className={`rounded border ${k.active ? 'border-gray-800 bg-gray-900' : 'border-gray-800/40 bg-gray-900/40'} px-4 py-3 text-sm`}>
            <div className="flex justify-between items-start">
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <span className={`text-xs font-medium ${k.active ? 'text-white' : 'text-gray-500'}`}>{k.name}</span>
                  {!k.active && (
                    <span className="text-xs bg-red-900/50 text-red-400 px-1.5 py-0.5 rounded">revoked</span>
                  )}
                </div>
                <p className="text-gray-500 text-xs font-mono">{k.key_prefix}…</p>
                <p className="text-gray-600 text-xs">
                  Created {new Date(k.created_at).toLocaleDateString()}
                  {k.last_used_at && ` · Last used ${new Date(k.last_used_at).toLocaleDateString()}`}
                </p>
              </div>
              {k.active && (
                <button
                  onClick={() => handleRevoke(k.id)}
                  className="text-gray-600 hover:text-red-400 text-xs transition-colors"
                >
                  revoke
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
