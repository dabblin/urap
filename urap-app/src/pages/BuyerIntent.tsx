import { useState } from 'react';
import type { ContactResult } from '../types.js';

const ENGINE = 'http://localhost:8080';
const TENANT = 'dev-tenant';
const API_KEY = '';

interface ScoredContact {
  score: number;
  lead_id: string;
  name: string;
  title: string;
  company: string;
  email: string;
  global_status: string;
  enrichment_source: string;
  email_verified: boolean;
  intent_signals: string[];
}

function scoreColor(score: number): string {
  if (score >= 60) return 'text-green-400';
  if (score >= 30) return 'text-yellow-400';
  return 'text-gray-500';
}

function scoreBadge(score: number): string {
  if (score >= 60) return 'bg-green-900 text-green-300';
  if (score >= 30) return 'bg-yellow-900 text-yellow-300';
  return 'bg-gray-800 text-gray-400';
}

interface Props {
  onSelectLead?: (lead: ContactResult | null) => void;
}

export function BuyerIntent({ onSelectLead }: Props) {
  const [contacts, setContacts] = useState<ScoredContact[]>([]);
  const [domain, setDomain] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleScore() {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${ENGINE}/outreach/intent/score`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': API_KEY,
          'x-tenant-id': TENANT,
        },
        body: JSON.stringify({ domain: domain || undefined, limit: 50 }),
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      setContacts(data.contacts || []);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }

  function toContactResult(c: ScoredContact): ContactResult {
    return {
      leadId: c.lead_id,
      name: c.name,
      title: c.title,
      company: c.company,
      email: c.email,
      globalStatus: c.global_status,
      emailVerified: c.email_verified,
      enrichmentSource: c.enrichment_source,
      intentSignals: c.intent_signals || [],
    };
  }

  return (
    <div className="flex flex-col h-full p-4 gap-4">
      <div className="flex gap-3 items-center">
        <input
          className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 w-64"
          placeholder="Filter by domain (optional)"
          value={domain}
          onChange={e => setDomain(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleScore()}
        />
        <button
          onClick={handleScore}
          disabled={loading}
          className="bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white text-sm font-medium rounded px-4 py-2 transition-colors"
        >
          {loading ? 'Scoring…' : 'Score Contacts'}
        </button>
        <span className="text-xs text-gray-500 ml-2">
          Sprint 4 adds 3rd-party intent signals (job changes, site visits, tech installs)
        </span>
      </div>

      {error && <p className="text-red-400 text-sm">{error}</p>}

      {contacts.length > 0 && (
        <div className="flex-1 overflow-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-gray-500 uppercase tracking-wider border-b border-gray-800">
                <th className="text-left py-2 pr-4">Score</th>
                <th className="text-left py-2 pr-4">Name</th>
                <th className="text-left py-2 pr-4">Title</th>
                <th className="text-left py-2 pr-4">Company</th>
                <th className="text-left py-2 pr-4">Email</th>
                <th className="text-left py-2 pr-4">Status</th>
                <th className="text-left py-2">Source</th>
              </tr>
            </thead>
            <tbody>
              {contacts.map(c => (
                <tr
                  key={c.lead_id}
                  className="border-b border-gray-900 hover:bg-gray-900 cursor-pointer transition-colors"
                  onClick={() => onSelectLead?.(toContactResult(c))}
                >
                  <td className="py-2 pr-4">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-bold ${scoreBadge(c.score)}`}>
                      {c.score}
                    </span>
                  </td>
                  <td className={`py-2 pr-4 font-medium ${scoreColor(c.score)}`}>{c.name}</td>
                  <td className="py-2 pr-4 text-gray-400">{c.title || '—'}</td>
                  <td className="py-2 pr-4 text-gray-300">{c.company}</td>
                  <td className="py-2 pr-4 text-gray-400">{c.email}</td>
                  <td className="py-2 pr-4">
                    <span className="px-2 py-0.5 rounded text-xs bg-gray-800 text-gray-300 capitalize">
                      {c.global_status.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="py-2 text-xs text-gray-500 capitalize">{c.enrichment_source}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {contacts.length === 0 && !loading && !error && (
        <div className="flex-1 flex items-center justify-center text-gray-600 text-sm">
          Click "Score Contacts" to rank your pipeline by intent.
        </div>
      )}
    </div>
  );
}
