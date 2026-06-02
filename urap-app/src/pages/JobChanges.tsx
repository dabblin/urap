import { useState } from 'react';

interface JobChange {
  lead_id: string;
  name: string;
  previous_title: string;
  new_title: string;
  company: string;
  email: string;
  detected_at: string;
  intent_boost: number;
}

export function JobChanges() {
  const [changes] = useState<JobChange[]>([]);

  return (
    <div className="flex flex-col h-full p-4 gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-200 uppercase tracking-wider">Job Change Monitor</h2>
        <span className="text-xs px-2 py-1 rounded bg-yellow-900 text-yellow-300 font-medium">
          Live signals — Sprint 4
        </span>
      </div>

      <div className="rounded border border-gray-800 bg-gray-900 p-4 text-sm text-gray-400">
        <p className="font-medium text-gray-200 mb-2">What ships in Sprint 4</p>
        <ul className="space-y-1 list-disc list-inside">
          <li>LinkedIn job change feed via Apify scraper (monitors your saved contact list)</li>
          <li>Auto-detection when a contact moves to a new company or gets a promotion</li>
          <li>Intent boost: +40 score when contact starts a new role (prime re-engagement window)</li>
          <li>Auto-trigger: new-role contacts re-enter top of outreach queue with personalized copy</li>
          <li>Supabase: <code className="text-xs bg-gray-800 px-1 rounded">urap_job_changes</code> table populated by Apify webhook</li>
        </ul>
      </div>

      {changes.length === 0 ? (
        <div className="flex-1 flex items-center justify-center text-gray-600 text-sm">
          No job changes detected yet. Live monitoring activates in Sprint 4.
        </div>
      ) : (
        <div className="flex-1 overflow-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-gray-500 uppercase tracking-wider border-b border-gray-800">
                <th className="text-left py-2 pr-4">Name</th>
                <th className="text-left py-2 pr-4">Previous Title</th>
                <th className="text-left py-2 pr-4">New Title</th>
                <th className="text-left py-2 pr-4">Company</th>
                <th className="text-left py-2 pr-4">Intent Boost</th>
                <th className="text-left py-2">Detected</th>
              </tr>
            </thead>
            <tbody>
              {changes.map(c => (
                <tr key={c.lead_id} className="border-b border-gray-900 hover:bg-gray-900">
                  <td className="py-2 pr-4 font-medium text-white">{c.name}</td>
                  <td className="py-2 pr-4 text-gray-500 line-through">{c.previous_title}</td>
                  <td className="py-2 pr-4 text-green-400">{c.new_title}</td>
                  <td className="py-2 pr-4 text-gray-300">{c.company}</td>
                  <td className="py-2 pr-4">
                    <span className="px-2 py-0.5 rounded text-xs bg-green-900 text-green-300 font-bold">
                      +{c.intent_boost}
                    </span>
                  </td>
                  <td className="py-2 text-xs text-gray-500">{c.detected_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
