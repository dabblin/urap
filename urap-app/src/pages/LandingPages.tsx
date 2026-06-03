import { useState, useEffect, useCallback } from 'react';
import { ENGINE, TENANT } from '../lib/config.js';

const API_KEY = '';
const HEADERS = {
  'Content-Type': 'application/json',
  'x-api-key': API_KEY,
  'x-tenant-id': TENANT,
};

const VERCEL_BASE = 'https://dabblin-landing-pages.vercel.app';

// ── Types ─────────────────────────────────────────────────────────────────────

interface CampaignPage {
  id: string;
  slug: string;
  headline: string;
  subheadline: string;
  cta_text: string;
  brand_color: string;
  form_fields: string[];
  company_name?: string;
  campaign_id?: string;
  created_at: string;
}

interface FormState {
  slug: string;
  headline: string;
  subheadline: string;
  cta_text: string;
  brand_color: string;
  form_fields: string[];
  company_name: string;
  logo_url: string;
}

const EMPTY_FORM: FormState = {
  slug: '',
  headline: '',
  subheadline: '',
  cta_text: 'Get Started',
  brand_color: '#6366f1',
  form_fields: ['name', 'email', 'phone'],
  company_name: '',
  logo_url: '',
};

const AVAILABLE_FIELDS = ['name', 'email', 'phone', 'company', 'title', 'zip'];

const PRESET_COLORS = [
  '#6366f1', '#8b5cf6', '#ec4899', '#f59e0b',
  '#10b981', '#3b82f6', '#ef4444', '#1a1a2e',
];

// ── Main ──────────────────────────────────────────────────────────────────────

export function LandingPages() {
  const [pages, setPages]     = useState<CampaignPage[]>([]);
  const [selected, setSelected] = useState<CampaignPage | null>(null);
  const [view, setView]       = useState<'idle' | 'builder'>('idle');
  const [form, setForm]       = useState<FormState>(EMPTY_FORM);
  const [saving, setSaving]   = useState(false);
  const [error, setError]     = useState<string | null>(null);
  const [copied, setCopied]   = useState<string | null>(null);

  const fetchPages = useCallback(async () => {
    try {
      const res = await fetch(`${ENGINE}/campaign-pages`, { headers: HEADERS });
      const data = await res.json();
      setPages(data.pages ?? []);
    } catch { /* silent */ }
  }, []);

  useEffect(() => { fetchPages(); }, [fetchPages]);

  function setField<K extends keyof FormState>(key: K, val: FormState[K]) {
    setForm(f => ({ ...f, [key]: val }));
  }

  function toggleFormField(field: string) {
    setForm(f => ({
      ...f,
      form_fields: f.form_fields.includes(field)
        ? f.form_fields.filter(x => x !== field)
        : [...f.form_fields, field],
    }));
  }

  async function handleSave() {
    if (!form.slug || !form.headline) return;
    setSaving(true);
    setError(null);
    try {
      const res = await fetch(`${ENGINE}/campaign-pages`, {
        method: 'POST', headers: HEADERS,
        body: JSON.stringify({
          slug:         form.slug.toLowerCase().replace(/\s+/g, '-'),
          headline:     form.headline,
          subheadline:  form.subheadline,
          cta_text:     form.cta_text,
          brand_color:  form.brand_color,
          form_fields:  form.form_fields,
          company_name: form.company_name || null,
          logo_url:     form.logo_url || null,
        }),
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      await fetchPages();
      setView('idle');
      setForm(EMPTY_FORM);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: string) {
    await fetch(`${ENGINE}/campaign-pages/${id}`, { method: 'DELETE', headers: HEADERS });
    setPages(p => p.filter(pg => pg.id !== id));
    if (selected?.id === id) { setSelected(null); setView('idle'); }
  }

  function copyUrl(slug: string) {
    const url = `${VERCEL_BASE}/c/${slug}`;
    navigator.clipboard.writeText(url);
    setCopied(slug);
    setTimeout(() => setCopied(null), 2000);
  }

  const canSave = !saving && !!form.slug && !!form.headline && form.form_fields.length > 0;

  return (
    <div className="flex h-full overflow-hidden">

      {/* ── Left: page list ─────────────────────────────────────────────────── */}
      <aside className="w-[280px] shrink-0 border-r border-gray-800 bg-gray-900 flex flex-col h-full">
        <div className="px-4 py-3 border-b border-gray-800 flex items-center justify-between shrink-0">
          <span className="text-sm font-semibold text-white">Landing Pages</span>
          <button
            onClick={() => { setView('builder'); setSelected(null); setForm(EMPTY_FORM); setError(null); }}
            className="text-xs px-2.5 py-1 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg transition-colors"
          >
            + New
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          {pages.length === 0 ? (
            <p className="text-gray-600 text-xs px-4 py-6">No pages yet.</p>
          ) : (
            pages.map(pg => (
              <div
                key={pg.id}
                onClick={() => { setSelected(pg); setView('idle'); }}
                className={`px-4 py-3 border-b border-gray-800/60 hover:bg-gray-800/50 transition-colors cursor-pointer
                  ${selected?.id === pg.id ? 'bg-gray-800' : ''}`}
              >
                <div className="flex items-center gap-2 mb-0.5">
                  <span
                    className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                    style={{ backgroundColor: pg.brand_color }}
                  />
                  <span className="text-sm text-white font-medium truncate">{pg.headline}</span>
                </div>
                <span className="text-xs text-gray-500 font-mono">/c/{pg.slug}</span>
              </div>
            ))
          )}
        </div>
      </aside>

      {/* ── Right panel ─────────────────────────────────────────────────────── */}
      <div className="flex-1 overflow-auto p-6">

        {/* Empty state */}
        {view === 'idle' && !selected && (
          <div className="flex flex-col items-center justify-center h-full text-center pb-16">
            <div className="text-4xl mb-4">🌐</div>
            <h2 className="text-white font-semibold text-lg mb-1">Campaign Landing Pages</h2>
            <p className="text-gray-500 text-sm max-w-xs">
              Build a hosted lead capture page for any campaign. Deployed on Vercel at{' '}
              <span className="text-gray-400 font-mono text-xs">dabblin-landing-pages.vercel.app/c/[slug]</span>
            </p>
            <button
              onClick={() => setView('builder')}
              className="mt-6 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm rounded-lg transition-colors"
            >
              Create First Page
            </button>
          </div>
        )}

        {/* Page detail */}
        {view === 'idle' && selected && (
          <div className="max-w-xl">
            <div className="flex items-start justify-between mb-6">
              <div>
                <h2 className="text-white text-lg font-semibold">{selected.headline}</h2>
                {selected.subheadline && <p className="text-gray-400 text-sm mt-0.5">{selected.subheadline}</p>}
              </div>
              <button
                onClick={() => handleDelete(selected.id)}
                className="text-xs text-red-500 hover:text-red-400 transition-colors ml-4 mt-1"
              >
                Delete
              </button>
            </div>

            {/* Live URL */}
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 mb-4">
              <p className="text-xs text-gray-500 mb-2 uppercase tracking-wider font-semibold">Live URL</p>
              <div className="flex items-center gap-2">
                <span className="text-sm text-indigo-400 font-mono flex-1 truncate">
                  {VERCEL_BASE}/c/{selected.slug}
                </span>
                <button
                  onClick={() => copyUrl(selected.slug)}
                  className="text-xs px-2.5 py-1 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors whitespace-nowrap"
                >
                  {copied === selected.slug ? '✓ Copied' : 'Copy'}
                </button>
                <a
                  href={`${VERCEL_BASE}/c/${selected.slug}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs px-2.5 py-1 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
                >
                  ↗
                </a>
              </div>
            </div>

            {/* Config summary */}
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 space-y-3 text-sm">
              <div className="flex gap-2">
                <span className="text-gray-600 w-28 shrink-0">CTA Button</span>
                <span className="text-gray-300">{selected.cta_text}</span>
              </div>
              <div className="flex gap-2 items-center">
                <span className="text-gray-600 w-28 shrink-0">Brand Color</span>
                <span
                  className="w-4 h-4 rounded-full border border-gray-700"
                  style={{ backgroundColor: selected.brand_color }}
                />
                <span className="text-gray-400 font-mono text-xs">{selected.brand_color}</span>
              </div>
              <div className="flex gap-2">
                <span className="text-gray-600 w-28 shrink-0">Form Fields</span>
                <span className="text-gray-300">{(selected.form_fields ?? []).join(', ')}</span>
              </div>
              {selected.company_name && (
                <div className="flex gap-2">
                  <span className="text-gray-600 w-28 shrink-0">Company</span>
                  <span className="text-gray-300">{selected.company_name}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Builder */}
        {view === 'builder' && (
          <div className="max-w-2xl space-y-5">
            <h2 className="text-white text-lg font-semibold">New Landing Page</h2>

            {/* Slug */}
            <div>
              <label className="block text-xs text-gray-400 mb-1.5">
                URL Slug <span className="text-red-400">*</span>
                <span className="text-gray-600 ml-2 font-mono text-[10px]">/c/your-slug</span>
              </label>
              <input
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500 font-mono"
                placeholder="insurance-leads-q3"
                value={form.slug}
                onChange={e => setField('slug', e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, '-'))}
              />
            </div>

            {/* Headline */}
            <div>
              <label className="block text-xs text-gray-400 mb-1.5">Headline <span className="text-red-400">*</span></label>
              <input
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500"
                placeholder="Get a Free Insurance Quote in 60 Seconds"
                value={form.headline}
                onChange={e => setField('headline', e.target.value)}
              />
            </div>

            {/* Subheadline */}
            <div>
              <label className="block text-xs text-gray-400 mb-1.5">Subheadline</label>
              <input
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500"
                placeholder="Compare top providers and save up to 40% on your premium."
                value={form.subheadline}
                onChange={e => setField('subheadline', e.target.value)}
              />
            </div>

            {/* CTA + Company row */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-gray-400 mb-1.5">CTA Button Text</label>
                <input
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500"
                  placeholder="Get My Quote"
                  value={form.cta_text}
                  onChange={e => setField('cta_text', e.target.value)}
                />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1.5">Company Name</label>
                <input
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500"
                  placeholder="Dabblin Cloud"
                  value={form.company_name}
                  onChange={e => setField('company_name', e.target.value)}
                />
              </div>
            </div>

            {/* Brand color */}
            <div>
              <label className="block text-xs text-gray-400 mb-2">Brand Color</label>
              <div className="flex items-center gap-3 flex-wrap">
                {PRESET_COLORS.map(c => (
                  <button
                    key={c}
                    onClick={() => setField('brand_color', c)}
                    className={`w-7 h-7 rounded-full border-2 transition-transform ${form.brand_color === c ? 'border-white scale-110' : 'border-transparent'}`}
                    style={{ backgroundColor: c }}
                  />
                ))}
                <input
                  type="color"
                  value={form.brand_color}
                  onChange={e => setField('brand_color', e.target.value)}
                  className="w-7 h-7 rounded-full border border-gray-700 bg-transparent cursor-pointer"
                  title="Custom color"
                />
                <span className="text-xs text-gray-500 font-mono">{form.brand_color}</span>
              </div>
            </div>

            {/* Form fields */}
            <div>
              <label className="block text-xs text-gray-400 mb-2">Form Fields</label>
              <div className="flex flex-wrap gap-2">
                {AVAILABLE_FIELDS.map(f => (
                  <button
                    key={f}
                    onClick={() => toggleFormField(f)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors capitalize
                      ${form.form_fields.includes(f)
                        ? 'bg-indigo-600 text-white'
                        : 'bg-gray-800 text-gray-400 hover:text-white border border-gray-700'}`}
                  >
                    {f}
                  </button>
                ))}
              </div>
              <p className="text-[11px] text-gray-600 mt-1.5">
                Selected: {form.form_fields.join(', ') || 'none'}
              </p>
            </div>

            {/* Logo URL */}
            <div>
              <label className="block text-xs text-gray-400 mb-1.5">Logo URL (optional)</label>
              <input
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500 font-mono"
                placeholder="https://yourdomain.com/logo.png"
                value={form.logo_url}
                onChange={e => setField('logo_url', e.target.value)}
              />
            </div>

            {/* Preview pill */}
            <div className="flex items-center gap-3 px-4 py-3 bg-gray-900/60 border border-gray-800 rounded-xl">
              <span
                className="w-3 h-3 rounded-full shrink-0"
                style={{ backgroundColor: form.brand_color }}
              />
              <span className="text-xs text-gray-400">
                Will deploy at{' '}
                <span className="text-indigo-400 font-mono">
                  {VERCEL_BASE}/c/{form.slug || 'your-slug'}
                </span>
              </span>
            </div>

            {error && (
              <div className="p-3 bg-red-900/30 border border-red-700/60 rounded-lg text-red-300 text-sm">{error}</div>
            )}

            <button
              onClick={handleSave}
              disabled={!canSave}
              className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white text-sm font-medium rounded-lg transition-colors"
            >
              {saving ? 'Saving…' : 'Create Page'}
            </button>

            <p className="text-xs text-gray-600 text-center">
              Page goes live instantly — Vercel serves it from the dabblin-landing-pages repo.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
