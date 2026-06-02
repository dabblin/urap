import { useState } from 'react';

const ENGINE = 'http://localhost:8080';
const TENANT = 'dev-tenant';
const API_KEY = '';

interface CallRecord {
  id: string;
  lead_id: string;
  to_number: string;
  call_sid: string;
  status: string;
  startedAt: string;
  duration?: string;
}

const STATUS_COLOR: Record<string, string> = {
  queued:      'text-yellow-400',
  ringing:     'text-yellow-300',
  'in-progress': 'text-green-400',
  completed:   'text-gray-400',
  busy:        'text-orange-400',
  'no-answer': 'text-orange-400',
  failed:      'text-red-400',
  canceled:    'text-gray-500',
  not_configured: 'text-red-400',
};

export function Calling() {
  const [leadId, setLeadId] = useState('');
  const [toNumber, setToNumber] = useState('');
  const [countryCode, setCountryCode] = useState('US');
  const [dialing, setDialing] = useState(false);
  const [callLog, setCallLog] = useState<CallRecord[]>([]);
  const [activeCall, setActiveCall] = useState<CallRecord | null>(null);
  const [hangingUp, setHangingUp] = useState(false);

  async function handleDial() {
    if (!leadId || !toNumber) return;
    setDialing(true);
    try {
      const res = await fetch(`${ENGINE}/voice/dial`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': API_KEY,
          'x-tenant-id': TENANT,
        },
        body: JSON.stringify({
          lead_id: leadId,
          to_number: toNumber,
          country_code: countryCode,
        }),
      });
      const data = await res.json();
      const record: CallRecord = {
        id: crypto.randomUUID(),
        lead_id: leadId,
        to_number: toNumber,
        call_sid: data.call_sid || '',
        status: data.status || (data.success ? 'queued' : 'failed'),
        startedAt: new Date().toLocaleTimeString(),
      };
      setCallLog(prev => [record, ...prev]);
      if (data.success && data.call_sid) {
        setActiveCall(record);
      }
    } catch (err) {
      console.error('[calling] dial error', err);
    } finally {
      setDialing(false);
    }
  }

  async function handleHangup() {
    if (!activeCall?.call_sid) return;
    setHangingUp(true);
    try {
      await fetch(`${ENGINE}/voice/hangup/${activeCall.call_sid}`, {
        method: 'POST',
        headers: { 'x-api-key': API_KEY, 'x-tenant-id': TENANT },
      });
      setCallLog(prev =>
        prev.map(c => c.call_sid === activeCall.call_sid ? { ...c, status: 'completed' } : c)
      );
      setActiveCall(null);
    } catch (err) {
      console.error('[calling] hangup error', err);
    } finally {
      setHangingUp(false);
    }
  }

  async function refreshStatus(call_sid: string) {
    try {
      const res = await fetch(`${ENGINE}/voice/status/${call_sid}`, {
        headers: { 'x-api-key': API_KEY, 'x-tenant-id': TENANT },
      });
      const data = await res.json();
      setCallLog(prev =>
        prev.map(c => c.call_sid === call_sid
          ? { ...c, status: data.status || c.status, duration: data.duration }
          : c
        )
      );
    } catch {/* silent */}
  }

  return (
    <div className="flex gap-4 h-full p-4 overflow-hidden">
      {/* Dialer panel */}
      <div className="w-72 flex-shrink-0 flex flex-col gap-3">
        <div>
          <h2 className="text-sm font-semibold text-gray-200 uppercase tracking-wider">Power Dialer</h2>
          <p className="text-xs text-gray-500 mt-1">Twilio-backed outbound calling with geo-routing</p>
        </div>

        <input
          className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
          placeholder="Lead ID *"
          value={leadId}
          onChange={e => setLeadId(e.target.value)}
        />

        <input
          className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 font-mono"
          placeholder="+1 (212) 555-0100 *"
          value={toNumber}
          onChange={e => setToNumber(e.target.value)}
        />

        <select
          className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
          value={countryCode}
          onChange={e => setCountryCode(e.target.value)}
        >
          <option value="US">US (+1)</option>
          <option value="CA">CA (+1)</option>
          <option value="GB">GB (+44)</option>
          <option value="AU">AU (+61)</option>
          <option value="DE">DE (+49)</option>
          <option value="FR">FR (+33)</option>
        </select>

        <button
          onClick={handleDial}
          disabled={dialing || !leadId || !toNumber || !!activeCall}
          className="bg-green-700 hover:bg-green-600 disabled:opacity-40 text-white text-sm font-medium rounded px-4 py-2 transition-colors flex items-center justify-center gap-2"
        >
          {dialing ? 'Dialing…' : '📞 Dial Lead'}
        </button>

        {activeCall && (
          <div className="rounded border border-green-800 bg-green-950/30 px-4 py-3 space-y-2">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              <span className="text-green-300 text-xs font-medium">Call active</span>
            </div>
            <p className="text-gray-400 text-xs font-mono">{activeCall.to_number}</p>
            <p className="text-gray-500 text-xs font-mono truncate">{activeCall.call_sid}</p>
            <div className="flex gap-2">
              <button
                onClick={handleHangup}
                disabled={hangingUp}
                className="flex-1 bg-red-800 hover:bg-red-700 disabled:opacity-40 text-white text-xs rounded px-3 py-1.5 transition-colors"
              >
                {hangingUp ? 'Ending…' : '🔴 Hang Up'}
              </button>
              <button
                onClick={() => refreshStatus(activeCall.call_sid)}
                className="bg-gray-700 hover:bg-gray-600 text-white text-xs rounded px-3 py-1.5 transition-colors"
              >
                ↻
              </button>
            </div>
          </div>
        )}

        <div className="text-xs text-gray-600 space-y-1 pt-1">
          <p>Provider: Twilio</p>
          <p>Geo-routing: IP → regional number</p>
          <p>TCPA gate enforced on SMS</p>
        </div>
      </div>

      {/* Call log */}
      <div className="flex-1 flex flex-col gap-2 overflow-auto">
        <h2 className="text-sm font-semibold text-gray-200 uppercase tracking-wider">Call Log</h2>

        {callLog.length === 0 && (
          <p className="text-gray-600 text-sm mt-4">No calls this session.</p>
        )}

        {callLog.map(call => (
          <div key={call.id} className="rounded border border-gray-800 bg-gray-900 px-4 py-3 text-sm">
            <div className="flex justify-between items-start">
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <span className="text-white font-mono text-xs">{call.to_number}</span>
                  <span className="text-gray-500 text-xs">lead: {call.lead_id}</span>
                </div>
                {call.call_sid && (
                  <p className="text-gray-600 text-xs font-mono">{call.call_sid.slice(0, 20)}…</p>
                )}
              </div>
              <div className="flex flex-col items-end gap-1">
                <span className={`text-xs font-medium ${STATUS_COLOR[call.status] || 'text-gray-400'}`}>
                  {call.status}
                </span>
                <span className="text-gray-600 text-xs">{call.startedAt}</span>
              </div>
            </div>
            {call.duration && (
              <p className="text-gray-500 text-xs mt-1">Duration: {call.duration}s</p>
            )}
            {call.call_sid && call.status !== 'completed' && call.status !== 'failed' && (
              <button
                onClick={() => refreshStatus(call.call_sid)}
                className="mt-2 text-xs text-gray-500 hover:text-gray-300 transition-colors"
              >
                ↻ refresh status
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
