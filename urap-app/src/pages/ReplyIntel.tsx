import { useState } from 'react';

import { ENGINE, TENANT } from '../lib/config.js';
const API_KEY = '';

interface ParseResult {
  lead_id: string;
  channel: string;
  sentiment: string;
  confidence: number;
  global_status_updated_to: string;
  calendar_link: string;
  telegram_sent: boolean;
  summary: string;
}

interface ParseLog {
  id: string;
  lead_id: string;
  channel: string;
  reply_snippet: string;
  result: ParseResult;
  parsedAt: string;
}

const SENTIMENT_BADGE: Record<string, string> = {
  meeting_request: 'bg-green-900 text-green-300',
  positive: 'bg-blue-900 text-blue-300',
  neutral: 'bg-gray-800 text-gray-400',
  negative: 'bg-red-900 text-red-400',
  unsubscribe: 'bg-orange-900 text-orange-400',
  out_of_office: 'bg-gray-800 text-gray-500',
};

const CHANNELS = ['email', 'sms', 'linkedin', 'voice'];

export function ReplyIntel() {
  const [leadId, setLeadId] = useState('');
  const [channel, setChannel] = useState('email');
  const [replyText, setReplyText] = useState('');
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState<ParseLog[]>([]);

  async function handleParse() {
    if (!leadId || !replyText.trim()) return;
    setLoading(true);
    try {
      const res = await fetch(`${ENGINE}/agents/reply/parse`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': API_KEY,
          'x-tenant-id': TENANT,
        },
        body: JSON.stringify({
          lead_id: leadId,
          channel,
          reply_text: replyText,
        }),
      });
      const data: ParseResult = await res.json();
      setLogs(prev => [{
        id: crypto.randomUUID(),
        lead_id: leadId,
        channel,
        reply_snippet: replyText.slice(0, 80),
        result: data,
        parsedAt: new Date().toLocaleTimeString(),
      }, ...prev]);
      setReplyText('');
    } catch (err) {
      console.error('[reply_intel] parse error', err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex gap-4 h-full p-4 overflow-hidden">
      {/* Input panel */}
      <div className="w-80 flex-shrink-0 flex flex-col gap-3">
        <div>
          <h2 className="text-sm font-semibold text-gray-200 uppercase tracking-wider">Reply Intelligence</h2>
          <p className="text-xs text-gray-500 mt-1">Parse incoming reply → classify → update status → alert</p>
        </div>

        <input
          className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
          placeholder="Lead ID *"
          value={leadId}
          onChange={e => setLeadId(e.target.value)}
        />

        <select
          className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
          value={channel}
          onChange={e => setChannel(e.target.value)}
        >
          {CHANNELS.map(ch => (
            <option key={ch} value={ch}>{ch}</option>
          ))}
        </select>

        <textarea
          className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 resize-none"
          rows={8}
          placeholder="Paste the reply text *"
          value={replyText}
          onChange={e => setReplyText(e.target.value)}
        />

        <button
          onClick={handleParse}
          disabled={loading || !leadId || !replyText.trim()}
          className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white text-sm font-medium rounded px-4 py-2 transition-colors"
        >
          {loading ? 'Parsing…' : '🧠 Parse Reply'}
        </button>

        <div className="text-xs text-gray-600 space-y-1">
          <p>Classifier: Claude Sonnet 4.6</p>
          <p>Fallback: keyword heuristics</p>
          <p>meeting_request → Calendar + Telegram</p>
        </div>
      </div>

      {/* Parse log */}
      <div className="flex-1 flex flex-col gap-2 overflow-auto">
        <h2 className="text-sm font-semibold text-gray-200 uppercase tracking-wider">Parse Log</h2>

        {logs.length === 0 && (
          <p className="text-gray-600 text-sm mt-4">No replies parsed this session.</p>
        )}

        {logs.map(log => (
          <div key={log.id} className="rounded border border-gray-800 bg-gray-900 px-4 py-3 text-sm space-y-2">
            <div className="flex justify-between items-start">
              <div>
                <span className="text-white font-medium text-xs font-mono">{log.lead_id}</span>
                <span className="text-gray-500 ml-2 text-xs">via {log.channel}</span>
              </div>
              <span className="text-gray-500 text-xs">{log.parsedAt}</span>
            </div>

            <p className="text-gray-500 text-xs italic truncate">"{log.reply_snippet}…"</p>

            <div className="flex flex-wrap gap-2 items-center">
              <span className={`text-xs px-2 py-0.5 rounded-full ${SENTIMENT_BADGE[log.result.sentiment] || 'bg-gray-800 text-gray-400'}`}>
                {log.result.sentiment}
              </span>
              <span className="text-gray-500 text-xs">
                {Math.round(log.result.confidence * 100)}% confidence
              </span>
              <span className="text-gray-400 text-xs">
                → <span className="text-white">{log.result.global_status_updated_to}</span>
              </span>
            </div>

            {log.result.summary && (
              <p className="text-gray-400 text-xs">{log.result.summary}</p>
            )}

            <div className="flex gap-3 text-xs">
              {log.result.calendar_link && (
                <a
                  href={log.result.calendar_link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-400 hover:underline"
                >
                  📅 Calendar Event
                </a>
              )}
              {log.result.telegram_sent && (
                <span className="text-green-400">✓ Telegram sent</span>
              )}
              {!log.result.telegram_sent && log.result.global_status_updated_to === 'meeting_set' && (
                <span className="text-gray-500">Telegram not configured</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
