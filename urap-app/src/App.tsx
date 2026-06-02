import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useState } from 'react';
import { TopNav } from './components/layout/TopNav.js';
import { Sidebar } from './components/layout/Sidebar.js';
import { getAllTools } from './registry.js';
import { Prospector } from './pages/Prospector.js';
import { Emailing } from './pages/Emailing.js';
import { BuyerIntent } from './pages/BuyerIntent.js';
import { JobChanges } from './pages/JobChanges.js';
import { Connect } from './pages/Connect.js';
import { WarpMode } from './pages/WarpMode.js';
import { AutoPilot } from './pages/AutoPilot.js';
import { ReplyIntel } from './pages/ReplyIntel.js';
import { Calling } from './pages/Calling.js';
import { CompaniesSearch } from './pages/CompaniesSearch.js';
import { Integrations } from './pages/Integrations.js';
import { ApiKeys } from './pages/ApiKeys.js';
import { BulkEnrich } from './pages/BulkEnrich.js';

type SelectedLead = {
  name: string;
  title: string;
  company: string;
  email: string;
  globalStatus: string;
} | null;

export default function App() {
  const [selectedLead, setSelectedLead] = useState<SelectedLead>(null);
  const tools = getAllTools();

  return (
    <BrowserRouter>
      <div className="flex flex-col h-screen bg-gray-950 text-white overflow-hidden">
        <TopNav />
        <div className="flex flex-1 min-h-0">
          <Sidebar />
          <main className="flex-1 overflow-auto bg-gray-950">
            <Routes>
              <Route path="/prospector" element={<Prospector onSelectLead={setSelectedLead} />} />
              <Route path="/companies" element={<CompaniesSearch />} />
              <Route path="/emailing" element={<Emailing onSelectLead={setSelectedLead} />} />
              <Route path="/buyer-intent" element={<BuyerIntent onSelectLead={setSelectedLead} />} />
              <Route path="/job-changes" element={<JobChanges />} />
              <Route path="/connect" element={<Connect onSelectLead={setSelectedLead} />} />
              <Route path="/warp-mode" element={<WarpMode />} />
              <Route path="/autopilot" element={<AutoPilot />} />
              <Route path="/reply-intel" element={<ReplyIntel />} />
              <Route path="/calling" element={<Calling />} />
              <Route path="/integrations" element={<Integrations />} />
              <Route path="/api-keys" element={<ApiKeys />} />
              <Route path="/bulk-credits" element={<BulkEnrich />} />
              <Route path="/" element={<Navigate to="/prospector" replace />} />
              {tools
                .filter(t => !['prospector', 'company-search', 'emailing', 'buyer-intent', 'job-changes', 'connect', 'warp-mode', 'autopilot', 'reply-intel', 'calling', 'integrations', 'api-keys', 'bulk-credits'].includes(t.id))
                .map(tool => (
                  <Route
                    key={tool.id}
                    path={tool.route}
                    element={
                      <div className="flex items-center justify-center h-full text-gray-600 text-sm">
                        {tool.label} — ships in Sprint {tool.sprint}
                      </div>
                    }
                  />
                ))}
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  );
}
