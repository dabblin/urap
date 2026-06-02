import { useState } from 'react';
import type { ContactResult } from '../types.js';

const ENGINE = 'http://localhost:8080';
const TENANT = 'dev-tenant';
const API_KEY = '';

interface EmailForm {
  toEmail: string;
  toName: string;
  fromEmail: string;
  fromName: string;
  subject: string;
  bodyHtml: string;
}

interface SendLog {
  id: string;
  toEmail: string;
  subject: string;
  success: boolean;
  provider: string;
  error?: string;
  sentAt: string;
}

const EMPTY_FORM: EmailForm = {
  toEmail: '',
  toName: '',
  fromEmail: '',
  fromName: '',
  subject: '',
  bodyHtml: '',
};

interface Props {
  onSelectLead?: (lead: ContactResult | null) => void;
}

export function Emailing({ onSelectLead: _onSelectLead }: Props) {
  const [form, setForm] = useState<EmailForm>(EMPTY_FORM);
  const [logs, setLogs] = useState<SendLog[]>([]);
  const [loading, setLoading] = useState(false);
  const [leadId, setLeadId] = useState('');

  function setField(key: keyof EmailForm, value: string) {
    setForm(f => ({ ...f, [key]: value }));
  }

  async function handleSend() {
    if (!form.toEmail || !form.subject || !form.bodyHtml) return;
    setLoading(true);
    try {
      const res = await fetch(`${ENGINE}/outreach/email/send`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': API_KEY,
          'x-tenant-id': TENANT,
        },
        body: JSON.stringify({
          lead_id: leadId || crypto.randomUUID(),
          to_email: form.toEmail,
          to_name: form.toName,
          from_email: form.fromEmail,
          from_name: form.fromName,
          subject: form.subject,
          body_html: form.bodyHtml,
          require_consent: false,
        }),
      });
      const data = await res.json();
      setLogs(prev => [{
        id: crypto.randomUUID(),
        toEmail: form.toEmail,
        subject: form.subject,
        success: data.success,
        provider: data.provider,
        error: data.error,
        sentAt: new Date().toLocaleTimeString(),
      }, ...prev]);
      if (data.success) setForm(EMPTY_FORM);
    } catch (err) {
      setLogs(prev => [{
        id: crypto.randomUUID(),
        toEmail: form.toEmail,
        subject: form.subject,
        success: false,
        provider: 'none',
        error: String(err),
        sentAt: new Date().toLocaleTimeString(),
      }, ...prev]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex gap-4 h-full p-4">
      {/* Compose panel */}
      <div className="w-96 flex-shrink-0 flex flex-col gap-3">
        <h2 className="text-sm font-semibold text-gray-200 uppercase tracking-wider">Compose</h2>
        <input
          className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
          placeholder="Lead ID (optional)"
          value={leadId}
          onChange={e => setLeadId(e.target.value)}
        />
        <input
          className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
          placeholder="To Email *"
          value={form.toEmail}
          onChange={e => setField('toEmail', e.target.value)}
        />
        <input
          className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
          placeholder="To Name"
          value={form.toName}
          onChange={e => setField('toName', e.target.value)}
        />
        <input
          className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
          placeholder="From Email"
          value={form.fromEmail}
          onChange={e => setField('fromEmail', e.target.value)}
        />
        <input
          className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
          placeholder="From Name"
          value={form.fromName}
          onChange={e => setField('fromName', e.target.value)}
        />
        <input
          className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
          placeholder="Subject *"
          value={form.subject}
          onChange={e => setField('subject', e.target.value)}
        />
        <textarea
          className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 resize-none"
          rows={6}
          placeholder="HTML body *"
          value={form.bodyHtml}
          onChange={e => setField('bodyHtml', e.target.value)}
        />
        <button
          onClick={handleSend}
          disabled={loading || !form.toEmail || !form.subject || !form.bodyHtml}
          className="bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white text-sm font-medium rounded px-4 py-2 transition-colors"
        >
          {loading ? 'Sending…' : 'Send Email'}
        </button>
        <p className="text-xs text-gray-500">
          Waterfall: SMTP2GO → Brevo → Mailgun
        </p>
      </div>

      {/* Send log */}
      <div className="flex-1 flex flex-col gap-2 overflow-auto">
        <h2 className="text-sm font-semibold text-gray-200 uppercase tracking-wider">Send Log</h2>
        {logs.length === 0 && (
          <p className="text-gray-600 text-sm mt-4">No emails sent this session.</p>
        )}
        {logs.map(log => (
          <div
            key={log.id}
            className={`rounded border px-4 py-3 text-sm ${log.success ? 'border-green-800 bg-green-950' : 'border-red-800 bg-red-950'}`}
          >
            <div className="flex justify-between items-center">
              <span className="font-medium text-white">{log.toEmail}</span>
              <span className="text-xs text-gray-400">{log.sentAt}</span>
            </div>
            <div className="text-gray-300 mt-1">{log.subject}</div>
            <div className="flex gap-3 mt-1 text-xs">
              <span className={log.success ? 'text-green-400' : 'text-red-400'}>
                {log.success ? '✓ Sent' : '✗ Failed'}
              </span>
              <span className="text-gray-500">via {log.provider}</span>
              {log.error && <span className="text-red-400">{log.error}</span>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
