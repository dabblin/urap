import { useState } from 'react';
import type { ContactResult } from '../types.js';

import { ENGINE, TENANT } from '../lib/config.js';
const API_KEY = '';

interface Props {
  onSelectLead?: (lead: ContactResult | null) => void;
}

export function Connect({ onSelectLead }: Props) {
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [domain, setDomain] = useState('');
  const [title, setTitle] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ContactResult | null>(null);
  const [error, setError] = useState('');
  const [added, setAdded] = useState(false);

  async function handleFind() {
    if (!domain) return;
    setLoading(true);
    setError('');
    setResult(null);
    setAdded(false);
    try {
      const res = await fetch(`${ENGINE}/enrich`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': API_KEY,
          'x-tenant-id': TENANT,
        },
        body: JSON.stringify({
          domain,
          first_name: firstName || undefined,
          last_name: lastName || undefined,
          title: title || undefined,
        }),
      });
      const data = await res.json();
      const contacts = data.contacts || [];
      if (contacts.length === 0) {
        setError('No contact found. Try a different name or domain.');
        return;
      }
      const c = contacts[0];
      const contact: ContactResult = {
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
      setResult(contact);
      onSelectLead?.(contact);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleAddToSequence() {
    if (!result) return;
    // Sprint 3: stub — sequence runner ships Sprint 4 (Warp Mode)
    setAdded(true);
  }

  return (
    <div className="flex flex-col h-full p-4 gap-4 max-w-xl">
      <h2 className="text-sm font-semibold text-gray-200 uppercase tracking-wider">
        Connect — Find & Queue
      </h2>
      <p className="text-xs text-gray-500">
        One-click: enrich a contact from the waterfall, review, then add to a sequence.
      </p>

      <div className="flex gap-3">
        <input
          className="flex-1 bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
          placeholder="First name"
          value={firstName}
          onChange={e => setFirstName(e.target.value)}
        />
        <input
          className="flex-1 bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
          placeholder="Last name"
          value={lastName}
          onChange={e => setLastName(e.target.value)}
        />
      </div>
      <input
        className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
        placeholder="Company domain (e.g. stripe.com) *"
        value={domain}
        onChange={e => setDomain(e.target.value)}
        onKeyDown={e => e.key === 'Enter' && handleFind()}
      />
      <input
        className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
        placeholder="Title filter (optional)"
        value={title}
        onChange={e => setTitle(e.target.value)}
      />
      <button
        onClick={handleFind}
        disabled={loading || !domain}
        className="bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white text-sm font-medium rounded px-4 py-2 transition-colors"
      >
        {loading ? 'Finding…' : 'Find Contact'}
      </button>

      {error && <p className="text-red-400 text-sm">{error}</p>}

      {result && (
        <div className="rounded border border-gray-700 bg-gray-900 p-4 space-y-2">
          <div className="flex justify-between items-start">
            <div>
              <p className="font-semibold text-white">{result.name}</p>
              <p className="text-sm text-gray-400">{result.title} · {result.company}</p>
              <p className="text-sm text-blue-400 mt-1">{result.email}</p>
            </div>
            <div className="flex flex-col items-end gap-1">
              {result.emailVerified && (
                <span className="text-xs px-2 py-0.5 rounded bg-green-900 text-green-300">Verified</span>
              )}
              <span className="text-xs px-2 py-0.5 rounded bg-gray-800 text-gray-400 capitalize">
                {result.enrichmentSource}
              </span>
            </div>
          </div>
          <button
            onClick={handleAddToSequence}
            disabled={added}
            className="w-full mt-2 bg-emerald-700 hover:bg-emerald-600 disabled:opacity-50 text-white text-sm font-medium rounded px-4 py-2 transition-colors"
          >
            {added ? '✓ Added to sequence queue' : 'Add to Sequence'}
          </button>
          {added && (
            <p className="text-xs text-gray-500 text-center">
              Sequence runner (Warp Mode) ships Sprint 4.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
