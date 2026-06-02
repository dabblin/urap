import { useState } from 'react';
import { ENGINE, TENANT } from '../lib/config.js';
import type { ContactResult } from '../types.js';

// ── Env ───────────────────────────────────────────────────────────────────────

const USER_NAME  = (import.meta as unknown as { env: Record<string, string> }).env
  .VITE_USER_NAME  ?? 'there';

// ── Filter panel config — mirrors Seamless.AI Contacts Search ─────────────────

const FILTER_DEFS = [
  { id: 'domain',       label: 'Company Domain',  placeholder: 'stripe.com, shopify.com' },
  { id: 'titles',       label: 'Titles',           placeholder: 'VP Sales, CTO, Founder'  },
  { id: 'jobChanges',   label: 'Job Changes',      placeholder: 'Changed roles in 90 days'},
  { id: 'seniority',    label: 'Seniority',        placeholder: 'C-Suite, VP, Director'   },
  { id: 'department',   label: 'Department',       placeholder: 'Sales, Engineering, HR'  },
  { id: 'location',     label: 'Location',         placeholder: 'New York, San Francisco' },
  { id: 'keywords',     label: 'Keywords',         placeholder: 'SaaS, B2B, outbound'     },
  { id: 'industry',     label: 'Industry',         placeholder: 'Software, FinTech, Health'},
  { id: 'employeeSize', label: 'Employee Size',    placeholder: '100–500 employees'        },
  { id: 'revenue',      label: 'Revenue',          placeholder: '$1M – $50M ARR'           },
  { id: 'technologies', label: 'Technologies',     placeholder: 'Salesforce, HubSpot, AWS' },
] as const;

type FilterId     = (typeof FILTER_DEFS)[number]['id'];
type FilterValues = Record<FilterId, string>;

const EMPTY_FILTERS: FilterValues = Object.fromEntries(
  FILTER_DEFS.map(f => [f.id, ''])
) as FilterValues;

// ── Helpers ───────────────────────────────────────────────────────────────────

function normalizeContact(raw: Record<string, unknown>): ContactResult {
  return {
    leadId:           (raw.lead_id          ?? raw.leadId          ?? '') as string,
    name:             (raw.name             ?? '') as string,
    title:            (raw.title            ?? '') as string,
    company:          (raw.company          ?? '') as string,
    email:            (raw.email            ?? '') as string,
    phone:            raw.phone as string | undefined,
    linkedinUrl:      (raw.linkedin_url     ?? raw.linkedinUrl) as string | undefined,
    globalStatus:     (raw.global_status    ?? raw.globalStatus    ?? 'prospecting') as string,
    emailVerified:    (raw.email_verified   ?? raw.emailVerified   ?? false) as boolean,
    enrichmentSource: (raw.enrichment_source ?? raw.enrichmentSource ?? '') as string,
    intentSignals:    (raw.intent_signals   ?? raw.intentSignals   ?? []) as string[],
  };
}

function parseAiQuery(q: string): { domain: string; title: string } {
  const m = q.match(/\b[\w-]+\.(com|io|ai|co|net|org|app|us|tech|dev)\b/i);
  const domain = m ? m[0] : '';
  const title  = domain ? q.replace(m![0], '').replace(/\s{2,}/g, ' ').trim() : q;
  return { domain, title };
}

// ── Types ─────────────────────────────────────────────────────────────────────

interface SelectedLead {
  name: string; title: string; company: string; email: string; globalStatus: string;
}
interface ProspectorProps { onSelectLead: (lead: SelectedLead) => void; }

// ── FilterPanel ───────────────────────────────────────────────────────────────

interface FilterPanelProps {
  filters:        FilterValues;
  onChange:       (id: FilterId, val: string) => void;
  onSearch:       () => void;
  loading:        boolean;
  visible:        boolean;
  mobileOpen:     boolean;
  onMobileClose:  () => void;
}

function FilterPanel({ filters, onChange, onSearch, loading, visible, mobileOpen, onMobileClose }: FilterPanelProps) {
  const [expanded, setExpanded] = useState<Set<FilterId>>(new Set(['domain', 'titles']));

  function toggle(id: FilterId) {
    setExpanded(p => { const n = new Set(p); n.has(id) ? n.delete(id) : n.add(id); return n; });
  }

  const activeCount = Object.values(filters).filter(v => v.trim()).length;

  const panelContent = (
    <>
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-800 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-white">Filters</span>
          {activeCount > 0 && (
            <span className="px-1.5 py-0.5 text-[10px] font-bold leading-none bg-indigo-600 text-white rounded-full">
              {activeCount}
            </span>
          )}
        </div>
        <div className="flex items-center gap-0.5">
          <div className="hidden md:flex items-center gap-0.5">
            {[['📁','Save filter set'],['🔖','Saved searches'],['🕐','Search history']].map(([icon, title]) => (
              <button key={title} title={title}
                className="w-7 h-7 flex items-center justify-center text-gray-500
                           hover:text-gray-300 hover:bg-gray-800 rounded transition-colors text-sm">
                {icon}
              </button>
            ))}
          </div>
          <button
            onClick={onMobileClose}
            className="md:hidden w-8 h-8 flex items-center justify-center text-gray-400
                       hover:text-white text-xl leading-none"
          >
            ×
          </button>
        </div>
      </div>

      {/* Add to List */}
      <div className="px-3 py-2.5 border-b border-gray-800 shrink-0">
        <button className="w-full flex items-center justify-between px-3 py-1.5 text-sm
                           text-gray-300 bg-gray-800/60 hover:bg-gray-800 border border-gray-700
                           rounded-lg transition-colors">
          <span className="flex items-center gap-2"><span className="text-xs">📋</span>Add to List</span>
          <span className="text-gray-500 text-xs">▾</span>
        </button>
      </div>

      {/* Scrollable filter rows */}
      <div className="flex-1 overflow-y-auto">
        {FILTER_DEFS.map(def => {
          const open     = expanded.has(def.id);
          const hasValue = filters[def.id].trim().length > 0;
          return (
            <div key={def.id} className="border-b border-gray-800/50">
              <button
                onClick={() => toggle(def.id)}
                className="w-full flex items-center justify-between px-4 py-2.5
                           hover:bg-gray-800/40 transition-colors group"
              >
                <span className={`text-sm transition-colors ${
                  hasValue ? 'text-white font-medium' : 'text-gray-400 group-hover:text-gray-200'
                }`}>
                  {def.label}
                  {hasValue && <span className="ml-1.5 text-indigo-400 text-xs">●</span>}
                </span>
                <span className="text-gray-600 text-xl font-thin leading-none select-none">
                  {open ? '−' : '+'}
                </span>
              </button>
              {open && (
                <div className="px-3 pb-3">
                  <input
                    type="text"
                    placeholder={def.placeholder}
                    value={filters[def.id]}
                    onChange={e => onChange(def.id, e.target.value)}
                    className="w-full bg-gray-800 text-white text-sm px-3 py-2 rounded-lg
                               border border-gray-700 focus:border-indigo-500 outline-none
                               placeholder-gray-600 transition-colors"
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Search CTA */}
      <div className="p-3 border-t border-gray-800 shrink-0">
        <button
          onClick={() => { onSearch(); if (mobileOpen) onMobileClose(); }}
          disabled={loading}
          className="w-full py-2.5 bg-gray-700 hover:bg-gray-600 text-white text-sm
                     font-medium rounded-lg transition-colors disabled:opacity-50"
        >
          {loading ? 'Searching…' : 'Search'}
        </button>
      </div>
    </>
  );

  return (
    <>
      {/* Mobile backdrop */}
      {mobileOpen && (
        <div
          className="md:hidden fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
          onClick={onMobileClose}
        />
      )}

      {/* Mobile drawer */}
      <aside
        className={[
          'fixed inset-y-0 left-0 z-50 w-[300px] max-w-[85vw]',
          'bg-gray-900 border-r border-gray-800 flex flex-col',
          'transition-transform duration-200',
          mobileOpen ? 'translate-x-0' : '-translate-x-full',
          'md:hidden',
        ].join(' ')}
      >
        {panelContent}
      </aside>

      {/* Desktop aside */}
      {visible && (
        <aside className="hidden md:flex w-[272px] shrink-0 bg-gray-900 border-r border-gray-800 flex-col h-full">
          {panelContent}
        </aside>
      )}
    </>
  );
}

// ── Prospector ────────────────────────────────────────────────────────────────

export function Prospector({ onSelectLead }: ProspectorProps) {
  const [filters, setFilters]               = useState<FilterValues>(EMPTY_FILTERS);
  const [aiQuery, setAiQuery]               = useState('');
  const [results, setResults]               = useState<ContactResult[]>([]);
  const [loading, setLoading]               = useState(false);
  const [error, setError]                   = useState<string | null>(null);
  const [showFilters, setShowFilters]       = useState(true);
  const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);

  function updateFilter(id: FilterId, val: string) {
    setFilters(f => ({ ...f, [id]: val }));
  }

  async function runSearch(domain: string, title: string) {
    if (!domain.trim() && !title.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const bulk     = !domain.trim() || !title.trim();
      const endpoint = bulk ? '/enrich/bulk' : '/enrich';
      const body     = bulk
        ? { domain: (domain || title).trim(), limit: 25 }
        : { domain: domain.trim(), title: title.trim() };

      const resp = await fetch(`${ENGINE}${endpoint}`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json', 'x-tenant-id': TENANT },
        body:    JSON.stringify(body),
      });
      if (!resp.ok) throw new Error(`Engine ${resp.status}: ${await resp.text()}`);
      const data = await resp.json();
      setResults((data.contacts ?? []).map(normalizeContact));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  function handleFilterSearch() {
    runSearch(filters.domain, filters.titles);
  }

  function handleAiSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!aiQuery.trim()) return;
    const { domain, title } = parseAiQuery(aiQuery);
    setRecentSearches(p => [aiQuery, ...p.filter(q => q !== aiQuery)].slice(0, 10));
    runSearch(domain || filters.domain, title || filters.titles);
  }

  const statusBadge = (v: boolean) =>
    v ? 'bg-green-900/60 text-green-300 border border-green-800'
      : 'bg-yellow-900/40 text-yellow-400 border border-yellow-800/60';

  const sourceBadge = (s: string) =>
    ({ prospeo: 'bg-indigo-900/60 text-indigo-300',
       snov:    'bg-purple-900/60 text-purple-300',
       hunter:  'bg-orange-900/50 text-orange-300' } as Record<string, string>)[s]
    ?? 'bg-gray-800 text-gray-400';

  const showHero    = results.length === 0 && !loading;
  const showLoading = loading && results.length === 0;

  return (
    <div className="flex h-full overflow-hidden">

      {/* ── Filter panel (desktop aside + mobile drawer) ── */}
      <FilterPanel
        filters={filters}
        onChange={updateFilter}
        onSearch={handleFilterSearch}
        loading={loading}
        visible={showFilters}
        mobileOpen={mobileFiltersOpen}
        onMobileClose={() => setMobileFiltersOpen(false)}
      />

      {/* ── Main content ── */}
      <div className="relative flex-1 flex flex-col overflow-hidden">

        {/* Loading spinner (first search) */}
        {showLoading && (
          <div className="absolute inset-0 z-20 flex flex-col items-center justify-center
                          bg-gray-950/70 backdrop-blur-sm gap-3">
            <div className="w-9 h-9 border-2 border-indigo-500 border-t-transparent
                            rounded-full animate-spin" />
            <span className="text-sm text-gray-400">Finding contacts…</span>
          </div>
        )}

        {showHero ? (
          /* ── AI Search hero ─────────────────────────────────────────────── */
          <div className="flex-1 flex flex-col items-center justify-center px-8 pb-16">
            <div className="w-full max-w-2xl">

              {/* AI label */}
              <div className="flex items-center gap-1.5 mb-5">
                <span className="text-pink-400 text-sm">✨</span>
                <span className="text-pink-400 text-xs font-bold tracking-[0.2em] uppercase">
                  AI Search
                </span>
              </div>

              {/* Greeting */}
              <h1 className="text-[2rem] font-bold text-white leading-tight mb-1">
                Hi {USER_NAME},
              </h1>
              <h2 className="text-[2rem] font-bold text-indigo-400 leading-tight mb-8">
                Who can I help you find today?
              </h2>

              {/* Search input */}
              <form onSubmit={handleAiSearch} className="relative">
                <textarea
                  rows={3}
                  value={aiQuery}
                  onChange={e => setAiQuery(e.target.value)}
                  placeholder="Sales CTOs at fintech companies with 50–500 employees in the US"
                  className="w-full bg-gray-900 border border-gray-700 hover:border-gray-600
                             focus:border-indigo-500 text-white text-sm rounded-xl px-4 py-3.5
                             pr-40 resize-none outline-none placeholder-gray-600 transition-colors"
                  onKeyDown={e => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleAiSearch(e as unknown as React.FormEvent);
                    }
                  }}
                />
                <button
                  type="submit"
                  disabled={loading || !aiQuery.trim()}
                  className="absolute bottom-3 right-3 flex items-center gap-1.5 px-4 py-1.5
                             bg-gray-700 hover:bg-gray-600 text-white text-sm font-medium
                             rounded-lg transition-colors disabled:opacity-40 whitespace-nowrap"
                >
                  🔍 Search Contacts
                </button>
              </form>

              {/* Sub-actions row */}
              <div className="flex items-center gap-3 mt-3 text-xs text-gray-600 flex-wrap">
                {/* Mobile filter button */}
                <button
                  onClick={() => setMobileFiltersOpen(true)}
                  className="md:hidden flex items-center gap-1 hover:text-gray-300 transition-colors"
                >
                  ◧ Filters {Object.values(filters).filter(v => v.trim()).length > 0 ? `(${Object.values(filters).filter(v => v.trim()).length})` : ''}
                </button>
                {/* Desktop filter toggle */}
                <button
                  onClick={() => setShowFilters(f => !f)}
                  className="hidden md:flex items-center gap-1 hover:text-gray-300 transition-colors"
                >
                  {showFilters ? '◧ Hide Filters' : '◩ Show Filters'}
                </button>
                {recentSearches.length > 0 && (
                  <>
                    <span>|</span>
                    <button className="hover:text-gray-300 transition-colors">
                      🕐 Recent Searches
                    </button>
                  </>
                )}
                <span>|</span>
                <button className="hover:text-gray-300 transition-colors">
                  🔖 Saved Searches
                </button>
              </div>

              {error && (
                <div className="mt-5 p-3 bg-red-900/30 border border-red-700/60 rounded-lg
                                text-red-300 text-sm">
                  {error}
                </div>
              )}
            </div>
          </div>

        ) : (
          /* ── Results grid ───────────────────────────────────────────────── */
          <div className="flex-1 flex flex-col overflow-hidden">
            {/* Sticky toolbar */}
            <div className="shrink-0 px-4 py-2.5 bg-gray-950 border-b border-gray-800
                            flex items-center justify-between gap-2 flex-wrap">
              <div className="flex items-center gap-2 flex-wrap">
                {/* Mobile filter button */}
                <button
                  onClick={() => setMobileFiltersOpen(true)}
                  className="md:hidden text-xs text-indigo-400 border border-indigo-900/60
                             hover:border-indigo-700 px-2.5 py-1 rounded-lg transition-colors"
                >
                  ◧ Filters {Object.values(filters).filter(v => v.trim()).length > 0 ? `(${Object.values(filters).filter(v => v.trim()).length})` : ''}
                </button>
                {/* Desktop filter toggle */}
                <button
                  onClick={() => setShowFilters(f => !f)}
                  className="hidden md:block text-xs text-gray-500 hover:text-white transition-colors"
                >
                  {showFilters ? '◧ Hide Filters' : '◩ Show Filters'}
                </button>
                <span className="text-gray-800 text-xs">|</span>
                <span className="text-xs text-gray-400">
                  {loading ? 'Searching…' : `${results.length} contact${results.length !== 1 ? 's' : ''} found`}
                </span>
              </div>
              <button
                onClick={() => { setResults([]); setAiQuery(''); setError(null); }}
                className="text-xs text-gray-500 hover:text-gray-200 transition-colors"
              >
                ← New Search
              </button>
            </div>

            {error && (
              <div className="mx-5 mt-4 p-3 bg-red-900/30 border border-red-700/60 rounded-lg
                              text-red-300 text-sm shrink-0">
                {error}
              </div>
            )}

            <div className="flex-1 overflow-auto">
              <table className="w-full min-w-[600px] text-sm">
                <thead className="sticky top-0 z-10 bg-gray-950">
                  <tr className="border-b border-gray-800 text-xs text-gray-500 uppercase tracking-wider">
                    <th className="px-5 py-3 text-left font-medium">Name</th>
                    <th className="px-5 py-3 text-left font-medium">Title</th>
                    <th className="px-5 py-3 text-left font-medium">Company</th>
                    <th className="px-5 py-3 text-left font-medium">Email</th>
                    <th className="px-5 py-3 text-left font-medium">Verified</th>
                    <th className="px-5 py-3 text-left font-medium">Source</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((c, i) => (
                    <tr
                      key={c.leadId || i}
                      onClick={() => onSelectLead({
                        name: c.name, title: c.title, company: c.company,
                        email: c.email, globalStatus: c.globalStatus,
                      })}
                      className="border-b border-gray-800/50 hover:bg-gray-800/40
                                 cursor-pointer transition-colors"
                    >
                      <td className="px-5 py-3 text-white font-medium whitespace-nowrap">{c.name}</td>
                      <td className="px-5 py-3 text-gray-300 whitespace-nowrap">{c.title || '—'}</td>
                      <td className="px-5 py-3 text-gray-300 whitespace-nowrap">{c.company}</td>
                      <td className="px-5 py-3 text-gray-400 font-mono text-xs whitespace-nowrap">{c.email}</td>
                      <td className="px-5 py-3">
                        <span className={`inline-block px-2 py-0.5 rounded-full text-xs ${statusBadge(c.emailVerified)}`}>
                          {c.emailVerified ? 'Verified' : 'Unverified'}
                        </span>
                      </td>
                      <td className="px-5 py-3">
                        <span className={`inline-block px-2 py-0.5 rounded-full text-xs capitalize ${sourceBadge(c.enrichmentSource)}`}>
                          {c.enrichmentSource || '—'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
