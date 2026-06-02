import { useState, useEffect, useCallback } from 'react';

// ── Env ───────────────────────────────────────────────────────────────────────

const ENGINE_URL = (import.meta as unknown as { env: Record<string, string> }).env
  .VITE_ENGINE_URL ?? 'http://localhost:8080';
const TENANT_ID  = (import.meta as unknown as { env: Record<string, string> }).env
  .VITE_TENANT_ID  ?? 'local';
const USER_NAME  = (import.meta as unknown as { env: Record<string, string> }).env
  .VITE_USER_NAME  ?? 'there';

// ── Filter config ─────────────────────────────────────────────────────────────

const FILTER_DEFS = [
  { id: 'name',         label: 'Company',      placeholder: 'Stripe, Shopify…'          },
  { id: 'domain',       label: 'Domain',       placeholder: 'stripe.com'                },
  { id: 'location',     label: 'Location',     placeholder: 'New York, San Francisco'   },
  { id: 'keywords',     label: 'Keywords',     placeholder: 'SaaS, marketplace, B2B'    },
  { id: 'industry',     label: 'Industry',     placeholder: 'Software, FinTech, Health'  },
  { id: 'employeeSize', label: 'Employee Size', placeholder: '100–500 employees'         },
  { id: 'revenue',      label: 'Revenue',      placeholder: '$1M – $50M ARR'             },
  { id: 'technologies', label: 'Technologies', placeholder: 'Salesforce, AWS, Stripe'    },
  { id: 'yearFounded',  label: 'Year Founded', placeholder: '2015 – 2022'               },
  { id: 'funding',      label: 'Funding',      placeholder: 'Series A, Series B'         },
  { id: 'companyType',  label: 'Company Type', placeholder: 'Startup, Private, Public'   },
] as const;

type FilterId     = (typeof FILTER_DEFS)[number]['id'];
type FilterValues = Record<FilterId, string>;

const EMPTY_FILTERS = Object.fromEntries(
  FILTER_DEFS.map(f => [f.id, ''])
) as FilterValues;

// ── Types ─────────────────────────────────────────────────────────────────────

interface CompanyResult {
  name:          string;
  domain:        string;
  website:       string;
  yelp_id?:      string;
  industry:      string;
  description:   string;
  location:      string;
  headcount:     string;
  company_type:  string;
  technologies:  string[];
  email_pattern: string;
  contact_count: number;
  linkedin:      string;
  phone:         string;
  source:        string;
}

interface EnrichedContact {
  email:       string;
  first_name:  string;
  last_name:   string;
  title:       string;
  confidence:  number;
  source:      string;
  status:      'loading' | 'found' | 'not_found';
  linkedin?:   string;
  instagram?:  string;
  twitter?:    string;
  youtube?:    string;
}

interface SavedList {
  id:          string;
  name:        string;
  item_count:  number;
  created_at:  string;
}

interface ListItem {
  id:            string;
  company_name:  string;
  domain:        string;
  phone:         string;
  email:         string;
  contact_name:  string;
  contact_title: string;
  industry:      string;
  location:      string;
  source:        string;
}

// ── Listing-site guard ────────────────────────────────────────────────────────

const LISTING_DOMAINS = [
  'yelp.com', 'foursquare.com', 'facebook.com', 'instagram.com',
  'twitter.com', 'linkedin.com', 'tripadvisor.com',
];
function isListingDomain(s: string): boolean {
  return LISTING_DOMAINS.some(d => s.includes(d));
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function fmtDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  } catch { return iso; }
}

// ── ComposeModal ──────────────────────────────────────────────────────────────

interface ComposeModalProps {
  toEmail:   string;
  toName:    string;
  company:   string;
  onClose:   () => void;
  onSent:    (msg: string) => void;
  onDrip:    (toEmail: string, toName: string, company: string) => void;
}

function ComposeModal({ toEmail, toName, company, onClose, onSent, onDrip }: ComposeModalProps) {
  const [fromEmail, setFromEmail] = useState('');
  const [fromName,  setFromName]  = useState('');
  const [subject,   setSubject]   = useState('');
  const [body,      setBody]      = useState('');
  const [sending,   setSending]   = useState(false);
  const [error,     setError]     = useState('');

  async function handleSend() {
    if (!fromEmail || !subject || !body) { setError('From email, subject, and body are required.'); return; }
    setSending(true); setError('');
    try {
      const resp = await fetch(`${ENGINE_URL}/outreach/email/send`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json', 'x-tenant-id': TENANT_ID },
        body: JSON.stringify({
          lead_id:    toEmail,
          to_email:   toEmail,
          to_name:    toName,
          from_email: fromEmail,
          from_name:  fromName,
          subject,
          body_html:  body.replace(/\n/g, '<br>'),
        }),
      });
      const d = await resp.json();
      if (d.success || d.provider) {
        onSent(`✓ Email sent to ${toEmail}`);
        onClose();
      } else {
        setError(d.error || 'Send failed — check Brevo configuration.');
      }
    } catch (e) {
      setError(String(e));
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-gray-900 border border-gray-700 rounded-xl shadow-2xl w-full max-w-lg mx-4">
        <div className="px-5 py-4 border-b border-gray-800 flex items-center justify-between">
          <span className="text-sm font-semibold text-white">Compose Email</span>
          <button onClick={onClose} className="text-gray-600 hover:text-gray-300 text-lg leading-none">×</button>
        </div>

        <div className="px-5 py-4 space-y-3">
          <div>
            <label className="block text-[11px] text-gray-500 mb-1">To</label>
            <div className="text-sm text-gray-300 px-3 py-2 bg-gray-800/50 rounded-lg border border-gray-700">
              {toName ? `${toName} <${toEmail}>` : toEmail}
              {company && <span className="text-gray-500 ml-2">· {company}</span>}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] text-gray-500 mb-1">From Email</label>
              <input value={fromEmail} onChange={e => setFromEmail(e.target.value)}
                placeholder="you@yourdomain.com"
                className="w-full bg-gray-800 text-white text-sm px-3 py-2 rounded-lg border border-gray-700
                           focus:border-indigo-500 outline-none placeholder-gray-600 transition-colors" />
            </div>
            <div>
              <label className="block text-[11px] text-gray-500 mb-1">From Name</label>
              <input value={fromName} onChange={e => setFromName(e.target.value)}
                placeholder="Your Name"
                className="w-full bg-gray-800 text-white text-sm px-3 py-2 rounded-lg border border-gray-700
                           focus:border-indigo-500 outline-none placeholder-gray-600 transition-colors" />
            </div>
          </div>

          <div>
            <label className="block text-[11px] text-gray-500 mb-1">Subject</label>
            <input value={subject} onChange={e => setSubject(e.target.value)}
              placeholder="Quick question about {company}"
              className="w-full bg-gray-800 text-white text-sm px-3 py-2 rounded-lg border border-gray-700
                         focus:border-indigo-500 outline-none placeholder-gray-600 transition-colors" />
          </div>

          <div>
            <label className="block text-[11px] text-gray-500 mb-1">Message</label>
            <textarea value={body} onChange={e => setBody(e.target.value)}
              rows={6}
              placeholder={`Hi ${toName || 'there'},\n\n`}
              className="w-full bg-gray-800 text-white text-sm px-3 py-2 rounded-lg border border-gray-700
                         focus:border-indigo-500 outline-none placeholder-gray-600 transition-colors resize-none" />
          </div>

          {error && <div className="text-xs text-red-400">{error}</div>}
        </div>

        <div className="px-5 py-3 border-t border-gray-800 flex items-center justify-between">
          <button
            onClick={() => { onClose(); onDrip(toEmail, toName, company); }}
            className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
          >
            ↪ Set up drip sequence instead
          </button>
          <div className="flex items-center gap-2">
            <button onClick={onClose}
              className="px-4 py-1.5 text-xs text-gray-400 hover:text-gray-200 border border-gray-700 rounded-lg transition-colors">
              Cancel
            </button>
            <button onClick={handleSend} disabled={sending}
              className="px-4 py-1.5 text-xs bg-indigo-600 hover:bg-indigo-500 text-white font-medium
                         rounded-lg transition-colors disabled:opacity-40">
              {sending ? '⟳ Sending…' : '✉ Send Now'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── SequenceBuilderModal ──────────────────────────────────────────────────────

const DEFAULT_STEPS = [
  { step: 0, delay_days: 0,  subject: '', body_html: '' },
  { step: 1, delay_days: 3,  subject: '', body_html: '' },
  { step: 2, delay_days: 7,  subject: '', body_html: '' },
];

interface SequenceStep { step: number; delay_days: number; subject: string; body_html: string; }

interface SequenceBuilderProps {
  toEmail:  string;
  toName:   string;
  company:  string;
  onClose:  () => void;
  onQueued: (msg: string) => void;
}

function SequenceBuilderModal({ toEmail, toName, company, onClose, onQueued }: SequenceBuilderProps) {
  const [seqName,   setSeqName]   = useState(`${company || toEmail} Outreach`);
  const [fromEmail, setFromEmail] = useState('');
  const [fromName,  setFromName]  = useState('');
  const [steps,     setSteps]     = useState<SequenceStep[]>(DEFAULT_STEPS.map(s => ({ ...s })));
  const [activeTab, setActiveTab] = useState(0);
  const [saving,    setSaving]    = useState(false);
  const [error,     setError]     = useState('');

  function updateStep(idx: number, field: 'subject' | 'body_html', val: string) {
    setSteps(prev => prev.map((s, i) => i === idx ? { ...s, [field]: val } : s));
  }

  const DAY_LABELS = ['Day 0 (immediate)', 'Day 3 follow-up', 'Day 7 follow-up'];

  async function handleEnroll() {
    if (!fromEmail) { setError('From email is required.'); return; }
    if (steps.some(s => !s.subject || !s.body_html)) { setError('All 3 steps need a subject and body.'); return; }
    setSaving(true); setError('');
    try {
      // 1. Create sequence template
      const createResp = await fetch(`${ENGINE_URL}/outreach/sequence/create`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json', 'x-tenant-id': TENANT_ID },
        body: JSON.stringify({
          name: seqName,
          from_email: fromEmail,
          from_name:  fromName,
          steps: steps.map(s => ({ ...s, body_html: s.body_html.replace(/\n/g, '<br>') })),
        }),
      });
      const created = await createResp.json();
      if (!created.sequence_id) throw new Error(created.detail || 'Create failed');

      // 2. Enroll contact
      const enrollResp = await fetch(`${ENGINE_URL}/outreach/sequence/enroll`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json', 'x-tenant-id': TENANT_ID },
        body: JSON.stringify({
          sequence_id: created.sequence_id,
          to_email:    toEmail,
          to_name:     toName,
          company,
        }),
      });
      const enrolled = await enrollResp.json();
      if (!enrolled.enrollment_id) throw new Error('Enroll failed');

      onQueued(`✓ ${toEmail} enrolled — Day 0 email sends within the hour`);
      onClose();
    } catch (e) {
      setError(String(e));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-gray-900 border border-gray-700 rounded-xl shadow-2xl w-full max-w-xl mx-4">
        <div className="px-5 py-4 border-b border-gray-800 flex items-center justify-between">
          <span className="text-sm font-semibold text-white">3-Step Drip Sequence</span>
          <button onClick={onClose} className="text-gray-600 hover:text-gray-300 text-lg leading-none">×</button>
        </div>

        <div className="px-5 pt-4 space-y-3">
          <div className="grid grid-cols-3 gap-3">
            <div className="col-span-1">
              <label className="block text-[11px] text-gray-500 mb-1">Sequence Name</label>
              <input value={seqName} onChange={e => setSeqName(e.target.value)}
                className="w-full bg-gray-800 text-white text-xs px-3 py-2 rounded-lg border border-gray-700
                           focus:border-indigo-500 outline-none transition-colors" />
            </div>
            <div>
              <label className="block text-[11px] text-gray-500 mb-1">From Email</label>
              <input value={fromEmail} onChange={e => setFromEmail(e.target.value)}
                placeholder="you@domain.com"
                className="w-full bg-gray-800 text-white text-xs px-3 py-2 rounded-lg border border-gray-700
                           focus:border-indigo-500 outline-none placeholder-gray-600 transition-colors" />
            </div>
            <div>
              <label className="block text-[11px] text-gray-500 mb-1">From Name</label>
              <input value={fromName} onChange={e => setFromName(e.target.value)}
                placeholder="Your Name"
                className="w-full bg-gray-800 text-white text-xs px-3 py-2 rounded-lg border border-gray-700
                           focus:border-indigo-500 outline-none placeholder-gray-600 transition-colors" />
            </div>
          </div>

          <div className="text-[11px] text-gray-500 flex items-center gap-2">
            <span>Sending to:</span>
            <span className="text-gray-300">{toName ? `${toName} <${toEmail}>` : toEmail}</span>
            {company && <span className="text-gray-600">· {company}</span>}
          </div>
        </div>

        {/* Step tabs */}
        <div className="px-5 mt-4">
          <div className="flex gap-1 mb-3">
            {DAY_LABELS.map((label, i) => (
              <button key={i} onClick={() => setActiveTab(i)}
                className={`px-3 py-1.5 text-xs rounded-lg transition-colors ${
                  activeTab === i
                    ? 'bg-indigo-600 text-white'
                    : 'text-gray-400 hover:text-gray-200 bg-gray-800/60'
                }`}>
                {label}
                {steps[i].subject && <span className="ml-1.5 text-[8px] text-emerald-400">●</span>}
              </button>
            ))}
          </div>

          <div className="space-y-2.5 pb-4">
            <div>
              <label className="block text-[11px] text-gray-500 mb-1">Subject</label>
              <input
                value={steps[activeTab].subject}
                onChange={e => updateStep(activeTab, 'subject', e.target.value)}
                placeholder="Quick question about your business"
                className="w-full bg-gray-800 text-white text-sm px-3 py-2 rounded-lg border border-gray-700
                           focus:border-indigo-500 outline-none placeholder-gray-600 transition-colors"
              />
            </div>
            <div>
              <label className="block text-[11px] text-gray-500 mb-1">Message</label>
              <textarea
                value={steps[activeTab].body_html}
                onChange={e => updateStep(activeTab, 'body_html', e.target.value)}
                rows={5}
                placeholder={activeTab === 0 ? `Hi ${toName || 'there'},\n\n` : 'Following up on my previous email…'}
                className="w-full bg-gray-800 text-white text-sm px-3 py-2 rounded-lg border border-gray-700
                           focus:border-indigo-500 outline-none placeholder-gray-600 transition-colors resize-none"
              />
            </div>
          </div>
        </div>

        {error && <div className="px-5 pb-2 text-xs text-red-400">{error}</div>}

        <div className="px-5 py-3 border-t border-gray-800 flex items-center justify-end gap-2">
          <button onClick={onClose}
            className="px-4 py-1.5 text-xs text-gray-400 hover:text-gray-200 border border-gray-700 rounded-lg transition-colors">
            Cancel
          </button>
          <button onClick={handleEnroll} disabled={saving}
            className="px-4 py-1.5 text-xs bg-indigo-600 hover:bg-indigo-500 text-white font-medium
                       rounded-lg transition-colors disabled:opacity-40">
            {saving ? '⟳ Enrolling…' : '🚀 Enroll in Sequence'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── AutopilotModal ────────────────────────────────────────────────────────────

interface AutopilotResult {
  companies_found:   number;
  emails_discovered: number;
  enrolled:          number;
  sequence_id:       string;
}

interface AutopilotModalProps {
  onClose: () => void;
}

function AutopilotModal({ onClose }: AutopilotModalProps) {
  const [keywords,   setKeywords]   = useState('');
  const [location,   setLocation]   = useState('');
  const [industry,   setIndustry]   = useState('');
  const [limit,      setLimit]      = useState(25);
  const [sequences,  setSequences]  = useState<{ id: string; name: string; from_email: string }[]>([]);
  const [seqId,      setSeqId]      = useState('');
  const [running,    setRunning]    = useState(false);
  const [result,     setResult]     = useState<AutopilotResult | null>(null);
  const [error,      setError]      = useState('');

  useEffect(() => {
    fetch(`${ENGINE_URL}/outreach/sequences`, { headers: { 'x-tenant-id': TENANT_ID } })
      .then(r => r.json())
      .then(d => { setSequences(d.sequences ?? []); if (d.sequences?.length) setSeqId(d.sequences[0].id); })
      .catch(() => {});
  }, []);

  async function handleLaunch() {
    if (!seqId) { setError('Select a sequence first.'); return; }
    if (!keywords && !location && !industry) { setError('Add at least one ICP filter.'); return; }
    setRunning(true); setError(''); setResult(null);
    try {
      const resp = await fetch(`${ENGINE_URL}/outreach/autopilot/run-icp`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json', 'x-tenant-id': TENANT_ID },
        body: JSON.stringify({ keywords, location, industry, limit, sequence_id: seqId }),
      });
      if (!resp.ok) throw new Error(await resp.text());
      setResult(await resp.json());
    } catch (e) {
      setError(String(e));
    } finally {
      setRunning(false);
    }
  }

  const selectedSeq = sequences.find(s => s.id === seqId);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-gray-900 border border-gray-700 rounded-xl shadow-2xl w-full max-w-md mx-4">
        <div className="px-5 py-4 border-b border-gray-800 flex items-center justify-between">
          <div>
            <span className="text-sm font-semibold text-white">⚡ Autopilot</span>
            <span className="text-xs text-gray-500 ml-2">Search → Enrich → Enroll</span>
          </div>
          <button onClick={onClose} className="text-gray-600 hover:text-gray-300 text-lg leading-none">×</button>
        </div>

        {result ? (
          /* ── Results view ── */
          <div className="px-5 py-6 text-center space-y-4">
            <div className="text-3xl">🚀</div>
            <div className="text-white font-semibold">Autopilot complete</div>
            <div className="grid grid-cols-3 gap-3 mt-2">
              {[
                { label: 'Companies',  value: result.companies_found },
                { label: 'Emails',     value: result.emails_discovered },
                { label: 'Enrolled',   value: result.enrolled },
              ].map(({ label, value }) => (
                <div key={label} className="bg-gray-800 rounded-lg p-3">
                  <div className="text-xl font-bold text-white">{value}</div>
                  <div className="text-[10px] text-gray-500 mt-0.5">{label}</div>
                </div>
              ))}
            </div>
            {selectedSeq && (
              <div className="text-xs text-gray-500 mt-2">
                Enrolled into <span className="text-indigo-400">{selectedSeq.name}</span>
                <br />Day 0 emails send within the hour.
              </div>
            )}
            <button onClick={onClose}
              className="mt-2 px-6 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm
                         font-medium rounded-lg transition-colors">
              Done
            </button>
          </div>
        ) : (
          /* ── Config view ── */
          <>
            <div className="px-5 py-4 space-y-3">
              <div>
                <label className="block text-[11px] text-gray-500 mb-1">Keywords</label>
                <input value={keywords} onChange={e => setKeywords(e.target.value)}
                  placeholder="barbershops, dental clinics, gyms…"
                  className="w-full bg-gray-800 text-white text-sm px-3 py-2 rounded-lg border border-gray-700
                             focus:border-indigo-500 outline-none placeholder-gray-600 transition-colors" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] text-gray-500 mb-1">Location</label>
                  <input value={location} onChange={e => setLocation(e.target.value)}
                    placeholder="Atlanta, GA"
                    className="w-full bg-gray-800 text-white text-sm px-3 py-2 rounded-lg border border-gray-700
                               focus:border-indigo-500 outline-none placeholder-gray-600 transition-colors" />
                </div>
                <div>
                  <label className="block text-[11px] text-gray-500 mb-1">Industry</label>
                  <input value={industry} onChange={e => setIndustry(e.target.value)}
                    placeholder="Health, Retail…"
                    className="w-full bg-gray-800 text-white text-sm px-3 py-2 rounded-lg border border-gray-700
                               focus:border-indigo-500 outline-none placeholder-gray-600 transition-colors" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] text-gray-500 mb-1">Max companies</label>
                  <select value={limit} onChange={e => setLimit(Number(e.target.value))}
                    className="w-full bg-gray-800 text-white text-sm px-3 py-2 rounded-lg border border-gray-700
                               focus:border-indigo-500 outline-none transition-colors">
                    {[10, 25, 50].map(n => <option key={n} value={n}>{n}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-[11px] text-gray-500 mb-1">Enroll into sequence</label>
                  {sequences.length === 0 ? (
                    <div className="text-xs text-gray-600 py-2">
                      No sequences yet — create one first via the ↪ Drip button.
                    </div>
                  ) : (
                    <select value={seqId} onChange={e => setSeqId(e.target.value)}
                      className="w-full bg-gray-800 text-white text-sm px-3 py-2 rounded-lg border border-gray-700
                                 focus:border-indigo-500 outline-none transition-colors">
                      {sequences.map(s => (
                        <option key={s.id} value={s.id}>{s.name}</option>
                      ))}
                    </select>
                  )}
                </div>
              </div>

              {error && <div className="text-xs text-red-400">{error}</div>}

              {running && (
                <div className="text-xs text-indigo-400 flex items-center gap-2">
                  <div className="w-3 h-3 border border-indigo-500 border-t-transparent rounded-full animate-spin" />
                  Searching companies, enriching contacts, enrolling…
                </div>
              )}
            </div>

            <div className="px-5 py-3 border-t border-gray-800 flex items-center justify-end gap-2">
              <button onClick={onClose}
                className="px-4 py-1.5 text-xs text-gray-400 hover:text-gray-200 border border-gray-700 rounded-lg transition-colors">
                Cancel
              </button>
              <button onClick={handleLaunch} disabled={running || sequences.length === 0}
                className="px-4 py-1.5 text-xs bg-indigo-600 hover:bg-indigo-500 text-white font-medium
                           rounded-lg transition-colors disabled:opacity-40">
                {running ? '⟳ Running…' : '⚡ Launch Autopilot'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// ── FilterPanel ───────────────────────────────────────────────────────────────

interface FilterPanelProps {
  filters:       FilterValues;
  onChange:      (id: FilterId, val: string) => void;
  onSearch:      () => void;
  onAddToList:   () => void;
  loading:       boolean;
  visible:       boolean;
  hasResults:    boolean;
  mobileOpen:    boolean;
  onMobileClose: () => void;
}

function FilterPanel({ filters, onChange, onSearch, onAddToList, loading, visible, hasResults, mobileOpen, onMobileClose }: FilterPanelProps) {
  const [expanded, setExpanded] = useState<Set<FilterId>>(new Set(['name', 'domain']));

  function toggle(id: FilterId) {
    setExpanded(p => { const n = new Set(p); n.has(id) ? n.delete(id) : n.add(id); return n; });
  }

  const activeCount = Object.values(filters).filter(v => v.trim()).length;

  const panelContent = (
    <>
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

      <div className="px-3 py-2.5 border-b border-gray-800 shrink-0">
        <button
          onClick={onAddToList}
          disabled={!hasResults}
          className="w-full flex items-center justify-between px-3 py-1.5 text-sm
                     text-gray-300 bg-gray-800/60 hover:bg-gray-800 border border-gray-700
                     rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <span className="flex items-center gap-2"><span className="text-xs">📁</span>Add to List</span>
          <span className="text-gray-500 text-xs">▾</span>
        </button>
      </div>

      <div className="px-3 py-2 border-b border-gray-800 shrink-0">
        <button className="w-full flex items-center justify-center gap-1.5 px-3 py-1.5 text-xs
                           text-gray-400 border border-dashed border-gray-700 hover:border-gray-500
                           hover:text-gray-200 rounded-lg transition-colors">
          ↑ Upload Companies
        </button>
      </div>

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

// ── Source badge ──────────────────────────────────────────────────────────────

function SourceBadge({ source }: { source: string }) {
  const map: Record<string, string> = {
    google_places: 'bg-blue-900/50 text-blue-300 border border-blue-800/60',
    yelp:          'bg-red-900/50 text-red-300 border border-red-800/60',
    foursquare:    'bg-violet-900/50 text-violet-300 border border-violet-800/60',
    apollo:        'bg-green-900/50 text-green-300 border border-green-800/60',
    hunter:        'bg-orange-900/50 text-orange-300 border border-orange-800/60',
    snov:          'bg-purple-900/60 text-purple-300 border border-purple-800/60',
    placeholder:   'bg-gray-800 text-gray-500 border border-gray-700',
  };
  return (
    <span className={`inline-block px-2 py-0.5 rounded-full text-xs capitalize
                      ${map[source] ?? 'bg-gray-800 text-gray-400'}`}>
      {source}
    </span>
  );
}

// ── Social icons ─────────────────────────────────────────────────────────────

type SocialLinks = Pick<EnrichedContact, 'linkedin' | 'instagram' | 'twitter' | 'youtube'>;

function SocialIcons({ socials, compact = true }: { socials: SocialLinks; compact?: boolean }) {
  const platforms = [
    { key: 'linkedin',  abbr: 'in', name: 'LinkedIn',  href: socials.linkedin,  cls: 'bg-blue-900/40 text-blue-300 border-blue-800/50 hover:bg-blue-800/60' },
    { key: 'instagram', abbr: 'ig', name: 'Instagram', href: socials.instagram, cls: 'bg-pink-900/40 text-pink-300 border-pink-800/50 hover:bg-pink-800/60' },
    { key: 'twitter',   abbr: 'x',  name: 'Twitter/X', href: socials.twitter,   cls: 'bg-sky-900/40  text-sky-300  border-sky-800/50  hover:bg-sky-800/60'  },
    { key: 'youtube',   abbr: 'yt', name: 'YouTube',   href: socials.youtube,   cls: 'bg-red-900/40  text-red-300  border-red-800/50  hover:bg-red-800/60'  },
  ];
  const found = platforms.filter(p => p.href);
  if (found.length === 0) return compact ? <span className="text-gray-700 text-xs">—</span> : null;
  return (
    <div className="flex items-center gap-1.5 flex-wrap">
      {found.map(p => (
        <a
          key={p.key}
          href={p.href}
          target="_blank"
          rel="noopener noreferrer"
          title={p.name}
          onClick={e => e.stopPropagation()}
          className={`px-1.5 py-0.5 text-[10px] font-bold uppercase rounded border transition-colors ${p.cls}`}
        >
          {compact ? p.abbr : p.name}
        </a>
      ))}
    </div>
  );
}

// ── Email cell ────────────────────────────────────────────────────────────────

function EmailCell({ enr, onCopy }: { enr?: EnrichedContact; onCopy: (e: string) => void }) {
  if (!enr) return <span className="text-gray-700 text-xs">—</span>;
  if (enr.status === 'loading')
    return <span className="text-indigo-400 text-[11px] animate-pulse">Finding…</span>;
  if (enr.email)
    return (
      <button
        onClick={ev => { ev.stopPropagation(); onCopy(enr.email); }}
        title="Click to copy"
        className="text-[11px] text-emerald-400 hover:text-emerald-300 font-mono
                   transition-colors truncate max-w-[160px] block"
      >
        {enr.email}
      </button>
    );
  return <span className="text-gray-700 text-xs">—</span>;
}

// ── SaveListModal ─────────────────────────────────────────────────────────────

interface SaveListModalProps {
  resultCount:  number;
  emailCount:   number;
  saving:       boolean;
  onSave:       (name: string) => void;
  onCancel:     () => void;
}

function SaveListModal({ resultCount, emailCount, saving, onSave, onCancel }: SaveListModalProps) {
  const [name, setName] = useState('');

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-gray-900 border border-gray-700 rounded-xl shadow-2xl w-full max-w-sm mx-4">
        <div className="px-5 py-4 border-b border-gray-800 flex items-center justify-between">
          <span className="text-sm font-semibold text-white">Save to List</span>
          <button onClick={onCancel} className="text-gray-600 hover:text-gray-300 text-lg leading-none">×</button>
        </div>

        <div className="px-5 py-4 space-y-4">
          <div>
            <label className="block text-xs text-gray-500 mb-1.5">List Name</label>
            <input
              autoFocus
              type="text"
              placeholder="Atlanta Barbershops, Q3 Outreach…"
              value={name}
              onChange={e => setName(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && name.trim()) onSave(name.trim()); }}
              className="w-full bg-gray-800 text-white text-sm px-3 py-2.5 rounded-lg
                         border border-gray-700 focus:border-indigo-500 outline-none
                         placeholder-gray-600 transition-colors"
            />
          </div>

          <div className="text-xs text-gray-500 space-y-0.5">
            <div>{resultCount} compan{resultCount !== 1 ? 'ies' : 'y'} will be saved</div>
            {emailCount > 0 && (
              <div className="text-emerald-600">
                {emailCount} with discovered email{emailCount !== 1 ? 's' : ''}
              </div>
            )}
          </div>
        </div>

        <div className="px-5 py-3 border-t border-gray-800 flex items-center justify-end gap-2">
          <button
            onClick={onCancel}
            className="px-4 py-1.5 text-xs text-gray-400 hover:text-gray-200
                       border border-gray-700 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={() => { if (name.trim()) onSave(name.trim()); }}
            disabled={!name.trim() || saving}
            className="px-4 py-1.5 text-xs bg-indigo-600 hover:bg-indigo-500 text-white
                       font-medium rounded-lg transition-colors disabled:opacity-40"
          >
            {saving ? '⟳ Saving…' : '✓ Save to List'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── MyListsPanel ──────────────────────────────────────────────────────────────

interface MyListsPanelProps {
  lists:        SavedList[];
  loading:      boolean;
  onDelete:     (id: string) => void;
  onViewItems:  (list: SavedList) => void;
  onClose:      () => void;
}

function MyListsPanel({ lists, loading, onDelete, onViewItems, onClose }: MyListsPanelProps) {
  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <div className="shrink-0 px-5 py-3 bg-gray-950 border-b border-gray-800
                      flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold text-white">My Lists</span>
          <span className="text-[10px] text-gray-500">{lists.length} saved</span>
        </div>
        <button onClick={onClose} className="text-xs text-gray-500 hover:text-gray-200 transition-colors">
          ← Back to Results
        </button>
      </div>

      <div className="flex-1 overflow-auto">
        {loading ? (
          <div className="flex items-center justify-center h-32">
            <div className="w-5 h-5 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : lists.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 text-center px-8">
            <div className="text-3xl mb-3">📁</div>
            <div className="text-sm text-gray-400 font-medium mb-1">No saved lists yet</div>
            <div className="text-xs text-gray-600">
              Search for companies and click "Add to List" to save them here.
            </div>
          </div>
        ) : (
          <table className="w-full min-w-[480px] text-sm">
            <thead className="sticky top-0 z-10 bg-gray-950">
              <tr className="border-b border-gray-800 text-xs text-gray-500 uppercase tracking-wider">
                <th className="px-5 py-3 text-left font-medium">Name</th>
                <th className="px-5 py-3 text-left font-medium">Companies</th>
                <th className="px-5 py-3 text-left font-medium">Saved</th>
                <th className="px-5 py-3 text-left font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {lists.map(l => (
                <tr key={l.id}
                  className="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors">
                  <td className="px-5 py-3">
                    <button
                      onClick={() => onViewItems(l)}
                      className="text-sm font-medium text-white hover:text-indigo-300 transition-colors text-left"
                    >
                      {l.name}
                    </button>
                  </td>
                  <td className="px-5 py-3">
                    <span className="text-xs text-gray-400">{l.item_count}</span>
                  </td>
                  <td className="px-5 py-3">
                    <span className="text-xs text-gray-500">{fmtDate(l.created_at)}</span>
                  </td>
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => onViewItems(l)}
                        className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
                      >
                        View
                      </button>
                      <span className="text-gray-700">·</span>
                      <button
                        onClick={() => onDelete(l.id)}
                        className="text-xs text-gray-600 hover:text-red-400 transition-colors"
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

// ── ListItemsPanel ────────────────────────────────────────────────────────────

interface ListItemsPanelProps {
  list:     SavedList;
  items:    ListItem[];
  loading:  boolean;
  onBack:   () => void;
  onDelete: (id: string) => void;
  onCopy:   (text: string) => void;
}

function ListItemsPanel({ list, items, loading, onBack, onDelete, onCopy }: ListItemsPanelProps) {
  function exportCSV() {
    const cols = ['Company', 'Domain', 'Phone', 'Email', 'Contact Name', 'Title', 'Industry', 'Location', 'Source'];
    const rows = items.map(it => [
      it.company_name, it.domain, it.phone, it.email,
      it.contact_name, it.contact_title, it.industry, it.location, it.source,
    ].map(v => `"${String(v ?? '').replace(/"/g, '""')}"`).join(','));
    const csv  = [cols.join(','), ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = `${list.name.replace(/\s+/g, '_')}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <div className="shrink-0 px-5 py-3 bg-gray-950 border-b border-gray-800
                      flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button onClick={onBack} className="text-xs text-gray-500 hover:text-gray-200 transition-colors">
            ← My Lists
          </button>
          <span className="text-gray-700 text-xs">|</span>
          <span className="text-xs font-semibold text-white">{list.name}</span>
          <span className="text-[10px] text-gray-500">{items.length} companies</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={exportCSV}
            disabled={items.length === 0}
            className="flex items-center gap-1.5 px-3 py-1 text-xs
                       bg-gray-800 hover:bg-gray-700 text-gray-300
                       border border-gray-700 rounded-lg transition-colors disabled:opacity-40"
          >
            ⬇ Export CSV
          </button>
          <button
            onClick={() => onDelete(list.id)}
            className="flex items-center gap-1.5 px-3 py-1 text-xs
                       text-red-500 hover:text-red-400 border border-red-900/50
                       hover:border-red-700 rounded-lg transition-colors"
          >
            🗑 Delete List
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-auto">
        {loading ? (
          <div className="flex items-center justify-center h-32">
            <div className="w-5 h-5 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : (
          <table className="w-full min-w-[720px] text-sm">
            <thead className="sticky top-0 z-10 bg-gray-950">
              <tr className="border-b border-gray-800 text-xs text-gray-500 uppercase tracking-wider">
                <th className="px-5 py-3 text-left font-medium">Company</th>
                <th className="px-5 py-3 text-left font-medium">Domain</th>
                <th className="px-5 py-3 text-left font-medium">Phone</th>
                <th className="px-5 py-3 text-left font-medium">Email</th>
                <th className="px-5 py-3 text-left font-medium">Contact</th>
                <th className="px-5 py-3 text-left font-medium">Industry</th>
                <th className="px-5 py-3 text-left font-medium">Location</th>
                <th className="px-5 py-3 text-left font-medium">Source</th>
              </tr>
            </thead>
            <tbody>
              {items.map(it => (
                <tr key={it.id}
                  className="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors">
                  <td className="px-5 py-3">
                    <div className="font-medium text-white text-sm">{it.company_name}</div>
                  </td>
                  <td className="px-5 py-3">
                    {it.domain ? (
                      <a href={`https://${it.domain}`} target="_blank" rel="noopener noreferrer"
                         className="text-xs text-indigo-400 hover:text-indigo-300 font-mono transition-colors">
                        {it.domain}
                      </a>
                    ) : <span className="text-gray-700 text-xs">—</span>}
                  </td>
                  <td className="px-5 py-3 text-gray-400 text-xs">{it.phone || '—'}</td>
                  <td className="px-5 py-3">
                    {it.email ? (
                      <button
                        onClick={() => onCopy(it.email)}
                        className="text-[11px] text-emerald-400 hover:text-emerald-300 font-mono transition-colors"
                      >
                        {it.email}
                      </button>
                    ) : <span className="text-gray-700 text-xs">—</span>}
                  </td>
                  <td className="px-5 py-3">
                    {it.contact_name ? (
                      <div>
                        <div className="text-xs text-white">{it.contact_name}</div>
                        {it.contact_title && (
                          <div className="text-[10px] text-gray-500">{it.contact_title}</div>
                        )}
                      </div>
                    ) : <span className="text-gray-700 text-xs">—</span>}
                  </td>
                  <td className="px-5 py-3 text-gray-400 text-xs">{it.industry || '—'}</td>
                  <td className="px-5 py-3 text-gray-400 text-xs">{it.location || '—'}</td>
                  <td className="px-5 py-3"><SourceBadge source={it.source || 'placeholder'} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

// ── CompaniesSearch ───────────────────────────────────────────────────────────

export function CompaniesSearch() {
  const [filters, setFilters]               = useState<FilterValues>(EMPTY_FILTERS);
  const [aiQuery, setAiQuery]               = useState('');
  const [results, setResults]               = useState<CompanyResult[]>([]);
  const [loading, setLoading]               = useState(false);
  const [error, setError]                   = useState<string | null>(null);
  const [showFilters, setShowFilters]       = useState(true);
  const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const [selected, setSelected]           = useState<CompanyResult | null>(null);
  const [enrichMap, setEnrichMap]         = useState<Record<number, EnrichedContact>>({});
  const [enrichingAll, setEnrichingAll]   = useState(false);
  const [copied, setCopied]               = useState<string | null>(null);

  // ── Autopilot state ───────────────────────────────────────────────────────
  const [autopilotOpen, setAutopilotOpen]   = useState(false);

  // ── Outreach state ────────────────────────────────────────────────────────
  const [composeTarget, setComposeTarget]   = useState<{ email: string; name: string; company: string } | null>(null);
  const [dripTarget, setDripTarget]         = useState<{ email: string; name: string; company: string } | null>(null);
  const [outreachToast, setOutreachToast]   = useState<string | null>(null);

  function showOutreachToast(msg: string) {
    setOutreachToast(msg);
    setTimeout(() => setOutreachToast(null), 4000);
  }

  // ── List management state ──────────────────────────────────────────────────
  const [listModalOpen, setListModalOpen] = useState(false);
  const [listSaving, setListSaving]       = useState(false);
  const [myLists, setMyLists]             = useState<SavedList[]>([]);
  const [listsLoading, setListsLoading]   = useState(false);
  const [showMyLists, setShowMyLists]     = useState(false);
  const [expandedList, setExpandedList]   = useState<SavedList | null>(null);
  const [listItems, setListItems]         = useState<ListItem[]>([]);
  const [listItemsLoading, setListItemsLoading] = useState(false);
  const [listToast, setListToast]         = useState<string | null>(null);

  function updateFilter(id: FilterId, val: string) {
    setFilters(f => ({ ...f, [id]: val }));
  }

  async function runSearch(params: {
    domain?: string; name?: string; keywords?: string;
    location?: string; industry?: string;
  }) {
    const { domain='', name='', keywords='', location='', industry='' } = params;
    if (!domain && !name && !keywords && !location && !industry) return;
    setLoading(true);
    setError(null);
    setResults([]);
    setSelected(null);
    setEnrichMap({});
    setShowMyLists(false);
    setExpandedList(null);
    try {
      const body: Record<string, unknown> = { limit: 50 };
      if (domain)   body.domain   = domain;
      if (name)     body.name     = name;
      if (keywords) body.keywords = keywords;
      if (location) body.location = location;
      if (industry) body.industry = industry;
      const resp = await fetch(`${ENGINE_URL}/companies/search`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json', 'x-tenant-id': TENANT_ID },
        body:    JSON.stringify(body),
      });
      if (!resp.ok) throw new Error(`Engine ${resp.status}: ${await resp.text()}`);
      const data = await resp.json();
      setResults(data.companies ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  function handleFilterSearch() {
    runSearch({
      domain:   filters.domain,
      name:     filters.name,
      keywords: filters.keywords,
      location: filters.location,
      industry: filters.industry,
    });
  }

  function handleAiSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!aiQuery.trim()) return;
    setRecentSearches(p => [aiQuery, ...p.filter(q => q !== aiQuery)].slice(0, 10));

    const domainMatch = aiQuery.match(/\b[\w-]+\.(com|io|ai|co|net|org|app)\b/i);
    if (domainMatch) { runSearch({ domain: domainMatch[0] }); return; }

    const locMatch = aiQuery.match(/^(.+?)\s+in\s+(?:the\s+)?(.+)$/i);
    if (locMatch) { runSearch({ keywords: locMatch[1].trim(), location: locMatch[2].trim() }); return; }

    runSearch({ keywords: aiQuery.trim() });
  }

  // ── Contact discovery ──────────────────────────────────────────────────────

  async function enrichCompany(idx: number, c: CompanyResult) {
    setEnrichMap(m => ({
      ...m,
      [idx]: { email: '', first_name: '', last_name: '', title: '', confidence: 0, source: '', status: 'loading' },
    }));
    try {
      const cleanDomain  = isListingDomain(c.domain  || '') ? '' : (c.domain  || '');
      const cleanWebsite = isListingDomain(c.website || '') ? '' : (c.website || '');
      const resp = await fetch(`${ENGINE_URL}/companies/contact`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json', 'x-tenant-id': TENANT_ID },
        body:    JSON.stringify({ name: c.name, domain: cleanDomain, website: cleanWebsite, phone: c.phone, yelp_id: c.yelp_id || '' }),
      });
      if (!resp.ok) throw new Error('enrich failed');
      const d = await resp.json();
      setEnrichMap(m => ({
        ...m,
        [idx]: {
          email:      d.email      || '',
          first_name: d.first_name || '',
          last_name:  d.last_name  || '',
          title:      d.title      || '',
          confidence: d.confidence || 0,
          source:     d.source     || '',
          status:     d.email ? 'found' : 'not_found',
          linkedin:   d.linkedin   || '',
          instagram:  d.instagram  || '',
          twitter:    d.twitter    || '',
          youtube:    d.youtube    || '',
        },
      }));
    } catch {
      setEnrichMap(m => ({
        ...m,
        [idx]: { email: '', first_name: '', last_name: '', title: '', confidence: 0, source: 'error', status: 'not_found' },
      }));
    }
  }

  async function enrichAll() {
    if (enrichingAll || results.length === 0) return;
    setEnrichingAll(true);
    try {
      const BATCH = 5;
      for (let i = 0; i < results.length; i += BATCH) {
        await Promise.all(results.slice(i, i + BATCH).map((c, j) => enrichCompany(i + j, c)));
      }
    } finally {
      setEnrichingAll(false);
    }
  }

  function exportCSV() {
    if (results.length === 0) return;
    const cols = ['Company', 'Email', 'Contact Name', 'Title', 'Phone', 'Website', 'Industry', 'Location', 'Source'];
    const rows = results.map((c, i) => {
      const e = enrichMap[i];
      const contactName = e ? `${e.first_name} ${e.last_name}`.trim() : '';
      return [
        c.name, e?.email || '', contactName, e?.title || '',
        c.phone, c.website || c.domain, c.industry, c.location, c.source,
      ].map(v => `"${String(v ?? '').replace(/"/g, '""')}"`).join(',');
    });
    const csv  = [cols.join(','), ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = `urap-leads-${Date.now()}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  function copyToClipboard(text: string) {
    navigator.clipboard.writeText(text);
    setCopied(text);
    setTimeout(() => setCopied(null), 1500);
  }

  // ── List management ────────────────────────────────────────────────────────

  const loadLists = useCallback(async () => {
    setListsLoading(true);
    try {
      const resp = await fetch(`${ENGINE_URL}/companies/lists`, {
        headers: { 'x-tenant-id': TENANT_ID },
      });
      if (!resp.ok) return;
      const d = await resp.json();
      setMyLists(d.lists ?? []);
    } catch { /* silent */ } finally {
      setListsLoading(false);
    }
  }, []);

  useEffect(() => { loadLists(); }, [loadLists]);

  async function handleSaveList(name: string) {
    setListSaving(true);
    try {
      const items = results.map((c, i) => {
        const enr = enrichMap[i];
        return {
          name:          c.name,
          domain:        c.domain,
          website:       c.website,
          phone:         c.phone,
          email:         enr?.status === 'found' ? enr.email : '',
          contact_name:  enr?.status === 'found'
            ? `${enr.first_name} ${enr.last_name}`.trim()
            : '',
          contact_title: enr?.status === 'found' ? enr.title : '',
          industry:      c.industry,
          location:      c.location,
          source:        c.source,
        };
      });

      const resp = await fetch(`${ENGINE_URL}/companies/list/save`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json', 'x-tenant-id': TENANT_ID },
        body:    JSON.stringify({ name, items }),
      });
      if (!resp.ok) throw new Error('save failed');
      const d = await resp.json();
      setListModalOpen(false);
      setListToast(`✓ Saved ${d.count} companies to "${d.name}"`);
      setTimeout(() => setListToast(null), 3000);
      loadLists();
    } catch {
      setListModalOpen(false);
      setListToast('✗ Failed to save list — try again');
      setTimeout(() => setListToast(null), 3000);
    } finally {
      setListSaving(false);
    }
  }

  async function handleViewListItems(list: SavedList) {
    setExpandedList(list);
    setListItemsLoading(true);
    try {
      const resp = await fetch(`${ENGINE_URL}/companies/list/${list.id}`, {
        headers: { 'x-tenant-id': TENANT_ID },
      });
      if (!resp.ok) return;
      const d = await resp.json();
      setListItems(d.items ?? []);
    } catch { /* silent */ } finally {
      setListItemsLoading(false);
    }
  }

  async function handleDeleteList(id: string) {
    try {
      await fetch(`${ENGINE_URL}/companies/list/${id}`, {
        method:  'DELETE',
        headers: { 'x-tenant-id': TENANT_ID },
      });
      if (expandedList?.id === id) {
        setExpandedList(null);
        setListItems([]);
      }
      loadLists();
    } catch { /* silent */ }
  }

  // ── Render helpers ─────────────────────────────────────────────────────────

  const showHero    = results.length === 0 && !loading && !showMyLists;
  const showLoading = loading && results.length === 0;

  const selectedIdx    = selected ? results.indexOf(selected) : -1;
  const selectedEnrich = selectedIdx >= 0 ? enrichMap[selectedIdx] : undefined;

  const enrichedCount = Object.values(enrichMap).filter(e => e.status === 'found').length;

  return (
    <div className="flex h-full overflow-hidden">

      {/* ── Filter panel (desktop aside + mobile drawer) ── */}
      <FilterPanel
        filters={filters}
        onChange={updateFilter}
        onSearch={handleFilterSearch}
        onAddToList={() => setListModalOpen(true)}
        loading={loading}
        visible={showFilters}
        hasResults={results.length > 0}
        mobileOpen={mobileFiltersOpen}
        onMobileClose={() => setMobileFiltersOpen(false)}
      />

      {/* ── Main content ── */}
      <div className="relative flex-1 flex flex-col overflow-hidden">

        {showLoading && (
          <div className="absolute inset-0 z-20 flex flex-col items-center justify-center
                          bg-gray-950/70 backdrop-blur-sm gap-3">
            <div className="w-9 h-9 border-2 border-indigo-500 border-t-transparent
                            rounded-full animate-spin" />
            <span className="text-sm text-gray-400">Finding companies…</span>
          </div>
        )}

        {showHero ? (
          /* ── AI Search hero ── */
          <div className="flex-1 flex flex-col items-center justify-center px-8 pb-16">
            <div className="w-full max-w-2xl">
              <div className="flex items-center gap-1.5 mb-5">
                <span className="text-pink-400 text-sm">✨</span>
                <span className="text-pink-400 text-xs font-bold tracking-[0.2em] uppercase">
                  AI Search
                </span>
              </div>
              <h1 className="text-[2rem] font-bold text-white leading-tight mb-1">
                Hi {USER_NAME},
              </h1>
              <h2 className="text-[2rem] font-bold text-indigo-400 leading-tight mb-8">
                What companies can I help you find today?
              </h2>

              <form onSubmit={handleAiSearch} className="relative">
                <textarea
                  rows={3}
                  value={aiQuery}
                  onChange={e => setAiQuery(e.target.value)}
                  placeholder="Find barbershops in Atlanta"
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
                  🏢 Search Companies
                </button>
              </form>

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
                  <><span>|</span>
                  <button className="hover:text-gray-300 transition-colors">
                    🕐 Recent Searches
                  </button></>
                )}
                <span>|</span>
                <button
                  onClick={() => setAutopilotOpen(true)}
                  className="hover:text-gray-300 transition-colors"
                >
                  ⚡ Autopilot
                </button>
                <span>|</span>
                <button
                  onClick={() => { setShowMyLists(true); loadLists(); }}
                  className="hover:text-gray-300 transition-colors"
                >
                  📁 My Lists {myLists.length > 0 && `(${myLists.length})`}
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

        ) : showMyLists && !expandedList ? (
          /* ── My Lists panel ── */
          <MyListsPanel
            lists={myLists}
            loading={listsLoading}
            onDelete={handleDeleteList}
            onViewItems={handleViewListItems}
            onClose={() => setShowMyLists(false)}
          />

        ) : showMyLists && expandedList ? (
          /* ── List items panel ── */
          <ListItemsPanel
            list={expandedList}
            items={listItems}
            loading={listItemsLoading}
            onBack={() => setExpandedList(null)}
            onDelete={id => { handleDeleteList(id); setShowMyLists(false); }}
            onCopy={copyToClipboard}
          />

        ) : (
          /* ── Results ── */
          <div className="flex-1 flex overflow-hidden">

            {/* Results table */}
            <div className="flex-1 flex flex-col overflow-hidden">

              {/* Results toolbar */}
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
                  <button onClick={() => setShowFilters(f => !f)}
                    className="hidden md:block text-xs text-gray-500 hover:text-white transition-colors">
                    {showFilters ? '◧ Hide Filters' : '◩ Show Filters'}
                  </button>
                  <span className="text-gray-800 text-xs">|</span>
                  <span className="text-xs text-gray-400">
                    {loading
                      ? 'Searching…'
                      : `${results.length} compan${results.length !== 1 ? 'ies' : 'y'} found`}
                  </span>
                  {enrichedCount > 0 && (
                    <span className="text-xs text-emerald-500">
                      · {enrichedCount} email{enrichedCount !== 1 ? 's' : ''} found
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-1.5 flex-wrap">
                  <button
                    onClick={() => setAutopilotOpen(true)}
                    className="flex items-center gap-1 px-2.5 py-1 text-xs
                               bg-indigo-600/10 hover:bg-indigo-600/30 text-indigo-400
                               border border-indigo-900/60 hover:border-indigo-700
                               rounded-lg transition-colors"
                  >
                    ⚡ <span className="hidden sm:inline">Autopilot</span>
                  </button>
                  <button
                    onClick={() => { setShowMyLists(true); setSelected(null); loadLists(); }}
                    className="flex items-center gap-1 px-2.5 py-1 text-xs
                               text-gray-400 hover:text-white border border-gray-700
                               hover:border-gray-500 rounded-lg transition-colors"
                  >
                    📁 <span className="hidden sm:inline">My Lists {myLists.length > 0 && `(${myLists.length})`}</span>
                    <span className="sm:hidden">{myLists.length > 0 ? myLists.length : ''}</span>
                  </button>
                  <button
                    onClick={enrichAll}
                    disabled={enrichingAll || loading}
                    className="flex items-center gap-1 px-2.5 py-1 text-xs
                               bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300
                               border border-indigo-800/60 rounded-lg transition-colors
                               disabled:opacity-40"
                  >
                    {enrichingAll ? '⟳' : '✨'} <span className="hidden sm:inline">{enrichingAll ? 'Enriching…' : 'Enrich All'}</span>
                  </button>
                  <button
                    onClick={exportCSV}
                    disabled={results.length === 0}
                    className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 text-xs
                               bg-gray-800 hover:bg-gray-700 text-gray-300
                               border border-gray-700 rounded-lg transition-colors
                               disabled:opacity-40"
                  >
                    ⬇ Export
                  </button>
                  <button
                    onClick={() => { setResults([]); setAiQuery(''); setError(null); setSelected(null); setEnrichMap({}); }}
                    className="text-xs text-gray-500 hover:text-gray-200 transition-colors"
                  >
                    ← New
                  </button>
                </div>
              </div>

              {error && (
                <div className="mx-5 mt-4 p-3 bg-red-900/30 border border-red-700/60 rounded-lg
                                text-red-300 text-sm shrink-0">{error}</div>
              )}

              <div className="flex-1 overflow-auto">
                <table className="w-full min-w-[860px] text-sm">
                  <thead className="sticky top-0 z-10 bg-gray-950">
                    <tr className="border-b border-gray-800 text-xs text-gray-500 uppercase tracking-wider">
                      <th className="px-5 py-3 text-left font-medium">Company</th>
                      <th className="px-5 py-3 text-left font-medium">Website</th>
                      <th className="px-5 py-3 text-left font-medium">Phone</th>
                      <th className="px-5 py-3 text-left font-medium">Email</th>
                      <th className="px-5 py-3 text-left font-medium">Socials</th>
                      <th className="px-5 py-3 text-left font-medium">Industry</th>
                      <th className="px-5 py-3 text-left font-medium">Location</th>
                      <th className="px-5 py-3 text-left font-medium">Source</th>
                      <th className="px-5 py-3 text-left font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.map((c, i) => (
                      <tr
                        key={`${c.domain || c.name}-${i}`}
                        onClick={() => setSelected(c)}
                        className={`border-b border-gray-800/50 cursor-pointer transition-colors
                          ${selected === c
                            ? 'bg-indigo-600/10 border-l-2 border-l-indigo-500'
                            : 'hover:bg-gray-800/40'}`}
                      >
                        <td className="px-5 py-3">
                          <div className="font-medium text-white">{c.name}</div>
                          {c.headcount && (
                            <div className="text-xs text-gray-600">{c.headcount} emp.</div>
                          )}
                        </td>
                        <td className="px-5 py-3">
                          {c.domain && !isListingDomain(c.domain) ? (
                            <a href={`https://${c.domain}`} target="_blank" rel="noopener noreferrer"
                               onClick={e => e.stopPropagation()}
                               className="text-xs text-indigo-400 hover:text-indigo-300 font-mono transition-colors">
                              {c.domain}
                            </a>
                          ) : '—'}
                        </td>
                        <td className="px-5 py-3 text-gray-400 text-xs whitespace-nowrap">
                          {c.phone || '—'}
                        </td>
                        <td className="px-5 py-3">
                          <EmailCell enr={enrichMap[i]} onCopy={copyToClipboard} />
                        </td>
                        <td className="px-5 py-3">
                          {enrichMap[i]?.status === 'loading' ? (
                            <span className="text-indigo-400 text-[11px] animate-pulse">…</span>
                          ) : enrichMap[i] ? (
                            <SocialIcons socials={enrichMap[i]!} />
                          ) : (
                            <span className="text-gray-700 text-xs">—</span>
                          )}
                        </td>
                        <td className="px-5 py-3 text-gray-300 text-xs whitespace-nowrap">{c.industry || '—'}</td>
                        <td className="px-5 py-3 text-gray-300 text-xs whitespace-nowrap">{c.location || '—'}</td>
                        <td className="px-5 py-3"><SourceBadge source={c.source} /></td>
                        <td className="px-5 py-3">
                          <button
                            onClick={ev => { ev.stopPropagation(); enrichCompany(i, c); }}
                            disabled={enrichMap[i]?.status === 'loading'}
                            className="px-3 py-1 text-xs bg-gray-800 hover:bg-gray-700 text-gray-300
                                       hover:text-white border border-gray-700 rounded-lg
                                       transition-colors whitespace-nowrap disabled:opacity-40"
                          >
                            {enrichMap[i]?.status === 'loading' ? '⟳' : '🔍 Find Contact'}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Company detail panel — fixed overlay on mobile, aside on desktop */}
            {selected && (
              <aside className="fixed inset-0 z-30 md:static md:z-auto md:w-80 md:shrink-0 border-l border-gray-800 bg-gray-900 flex flex-col overflow-y-auto">
                <div className="p-4 border-b border-gray-800 flex items-start justify-between">
                  <div>
                    <div className="font-semibold text-white text-base">{selected.name}</div>
                    <div className="text-xs text-gray-500 font-mono mt-0.5">{selected.domain}</div>
                    {selected.company_type && (
                      <span className="inline-block mt-1.5 px-2 py-0.5 text-xs rounded-full
                                       bg-gray-800 text-gray-400 capitalize border border-gray-700">
                        {selected.company_type}
                      </span>
                    )}
                  </div>
                  <button onClick={() => setSelected(null)}
                    className="text-gray-600 hover:text-gray-300 text-lg leading-none">×</button>
                </div>

                {/* Contact card — shown after enrichment */}
                {selectedEnrich && selectedEnrich.status !== 'loading' && selectedEnrich.email && (
                  <div className="p-4 border-b border-gray-800 bg-emerald-950/20">
                    <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2.5">
                      Contact Found
                    </div>
                    {(selectedEnrich.first_name || selectedEnrich.last_name) && (
                      <div className="text-sm text-white font-medium mb-1">
                        {`${selectedEnrich.first_name} ${selectedEnrich.last_name}`.trim()}
                        {selectedEnrich.title && (
                          <span className="text-xs text-gray-500 ml-1.5 font-normal">
                            {selectedEnrich.title}
                          </span>
                        )}
                      </div>
                    )}
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xs text-emerald-400 font-mono break-all">
                        {selectedEnrich.email}
                      </span>
                      <button
                        onClick={() => copyToClipboard(selectedEnrich.email)}
                        className={`shrink-0 text-[10px] px-1.5 py-0.5 border rounded transition-colors ${
                          copied === selectedEnrich.email
                            ? 'border-emerald-600 text-emerald-400'
                            : 'border-gray-700 text-gray-600 hover:text-gray-300'
                        }`}
                      >
                        {copied === selectedEnrich.email ? '✓' : 'copy'}
                      </button>
                    </div>
                    {selectedEnrich.confidence > 0 && (
                      <div className="text-[10px] text-gray-600 mb-2.5">
                        {selectedEnrich.confidence}% confidence · {selectedEnrich.source}
                      </div>
                    )}
                    <div className="flex gap-2">
                      <button
                        onClick={() => setComposeTarget({
                          email:   selectedEnrich.email,
                          name:    `${selectedEnrich.first_name} ${selectedEnrich.last_name}`.trim(),
                          company: selected.name,
                        })}
                        className="flex-1 py-1.5 text-xs bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300
                                   border border-indigo-800/60 rounded-lg transition-colors text-center"
                      >
                        ✉ Send Email
                      </button>
                      <button
                        onClick={() => setDripTarget({
                          email:   selectedEnrich.email,
                          name:    `${selectedEnrich.first_name} ${selectedEnrich.last_name}`.trim(),
                          company: selected.name,
                        })}
                        className="flex-1 py-1.5 text-xs bg-gray-800 hover:bg-gray-700 text-gray-300
                                   border border-gray-700 rounded-lg transition-colors text-center"
                      >
                        ↪ Drip
                      </button>
                    </div>
                  </div>
                )}

                {/* Enrich CTA if not yet enriched */}
                {!selectedEnrich && (
                  <div className="p-4 border-b border-gray-800">
                    <button
                      onClick={() => enrichCompany(selectedIdx, selected)}
                      className="w-full py-2 bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300
                                 text-sm border border-indigo-800/60 rounded-lg transition-colors"
                    >
                      🔍 Find Contact Info
                    </button>
                  </div>
                )}

                {selectedEnrich?.status === 'loading' && (
                  <div className="p-4 border-b border-gray-800 flex items-center gap-2">
                    <div className="w-3 h-3 border border-indigo-500 border-t-transparent rounded-full animate-spin" />
                    <span className="text-xs text-gray-400">Searching for contact…</span>
                  </div>
                )}

                {selected.description && (
                  <div className="p-4 border-b border-gray-800">
                    <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                      About
                    </div>
                    <p className="text-sm text-gray-300 leading-relaxed">{selected.description}</p>
                  </div>
                )}

                <div className="p-4 border-b border-gray-800 space-y-2.5">
                  <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                    Details
                  </div>
                  {[
                    ['Industry',    selected.industry],
                    ['Size',        selected.headcount],
                    ['Location',    selected.location],
                    ['Phone',       selected.phone],
                    ['Email Format', selected.email_pattern ? `{first}@${selected.domain}` : ''],
                    ['Contacts',    selected.contact_count ? `${selected.contact_count} found` : ''],
                  ].map(([label, value]) => value && (
                    <div key={label} className="flex items-start gap-2">
                      <span className="text-xs text-gray-600 w-24 shrink-0 mt-0.5">{label}</span>
                      <span className="text-xs text-gray-300 break-all">{value}</span>
                    </div>
                  ))}
                </div>

                {selected.technologies.length > 0 && (
                  <div className="p-4 border-b border-gray-800">
                    <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                      Technologies
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {selected.technologies.map(t => (
                        <span key={t} className="px-2 py-0.5 text-xs bg-gray-800 text-gray-400
                                                  border border-gray-700 rounded">
                          {t}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Social profiles from enrichment */}
                {selectedEnrich && selectedEnrich.status !== 'loading' &&
                  (selectedEnrich.linkedin || selectedEnrich.instagram || selectedEnrich.twitter || selectedEnrich.youtube) && (
                  <div className="p-4 border-b border-gray-800">
                    <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2.5">
                      Social Profiles
                    </div>
                    <SocialIcons socials={selectedEnrich} compact={false} />
                  </div>
                )}

                {/* Fallback: LinkedIn from company search result when no enrichment yet */}
                {!selectedEnrich && selected.linkedin && (
                  <div className="p-4 border-b border-gray-800">
                    <a href={selected.linkedin.startsWith('http') ? selected.linkedin : `https://${selected.linkedin}`}
                       target="_blank" rel="noopener noreferrer"
                       className="flex items-center gap-2 text-xs text-indigo-400 hover:text-indigo-300 transition-colors">
                      🔗 View on LinkedIn
                    </a>
                  </div>
                )}

                <div className="p-4 border-t border-gray-800 mt-auto space-y-2">
                  <button
                    onClick={() => setListModalOpen(true)}
                    className="w-full py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 text-sm
                               border border-gray-700 rounded-lg transition-colors"
                  >
                    📁 Save Results to List
                  </button>
                  {selectedEnrich?.email ? (
                    <button
                      onClick={() => copyToClipboard(selectedEnrich.email)}
                      className="w-full py-2 bg-emerald-700 hover:bg-emerald-600 text-white text-sm
                                 font-medium rounded-lg transition-colors"
                    >
                      📋 Copy Email
                    </button>
                  ) : (
                    <button
                      onClick={() => enrichCompany(selectedIdx, selected)}
                      disabled={selectedEnrich?.status === 'loading'}
                      className="w-full py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm
                                 font-medium rounded-lg transition-colors disabled:opacity-50"
                    >
                      🔍 Find Contact at {selected.name}
                    </button>
                  )}
                </div>
              </aside>
            )}
          </div>
        )}
      </div>

      {/* ── Autopilot modal ── */}
      {autopilotOpen && (
        <AutopilotModal onClose={() => setAutopilotOpen(false)} />
      )}

      {/* ── Compose modal ── */}
      {composeTarget && (
        <ComposeModal
          toEmail={composeTarget.email}
          toName={composeTarget.name}
          company={composeTarget.company}
          onClose={() => setComposeTarget(null)}
          onSent={showOutreachToast}
          onDrip={(email, name, company) => { setComposeTarget(null); setDripTarget({ email, name, company }); }}
        />
      )}

      {/* ── Sequence builder modal ── */}
      {dripTarget && (
        <SequenceBuilderModal
          toEmail={dripTarget.email}
          toName={dripTarget.name}
          company={dripTarget.company}
          onClose={() => setDripTarget(null)}
          onQueued={showOutreachToast}
        />
      )}

      {/* ── Save List modal ── */}
      {listModalOpen && (
        <SaveListModal
          resultCount={results.length}
          emailCount={enrichedCount}
          saving={listSaving}
          onSave={handleSaveList}
          onCancel={() => setListModalOpen(false)}
        />
      )}

      {/* ── Outreach toast ── */}
      {outreachToast && (
        <div className="fixed bottom-20 md:bottom-16 left-1/2 -translate-x-1/2 z-50 px-4 py-2 bg-gray-800
                        border border-indigo-800 rounded-lg text-xs text-indigo-300 shadow-xl">
          {outreachToast}
        </div>
      )}

      {/* ── Copy toast ── */}
      {copied && (
        <div className="fixed bottom-20 md:bottom-6 left-1/2 -translate-x-1/2 z-50 px-4 py-2 bg-gray-800
                        border border-gray-700 rounded-lg text-xs text-emerald-400 shadow-xl">
          ✓ Copied to clipboard
        </div>
      )}

      {/* ── List save toast ── */}
      {listToast && (
        <div className={`fixed bottom-20 md:bottom-6 left-1/2 -translate-x-1/2 z-50 px-4 py-2 bg-gray-800
                         border rounded-lg text-xs shadow-xl ${
                           listToast.startsWith('✓')
                             ? 'border-emerald-800 text-emerald-400'
                             : 'border-red-800 text-red-400'
                         }`}>
          {listToast}
        </div>
      )}
    </div>
  );
}
