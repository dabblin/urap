import { useLocation, useNavigate } from 'react-router-dom';
import urapLogo from '../../assets/urap-logo.png';

// ── Nav tabs — mirrors Seamless.AI top navigation ─────────────────────────────

const NAV_TABS = [
  {
    label:  'Contacts Search',
    route:  '/prospector',
    routes: ['/prospector', '/buyer-intent', '/job-changes'],
  },
  {
    label:  'Companies Search',
    route:  '/companies',
    routes: ['/companies'],
  },
  {
    label:  'Search with Agent',
    route:  '/warp-mode',
    routes: ['/warp-mode'],
  },
  {
    label:  'Engagement',
    route:  '/emailing',
    routes: ['/connect', '/emailing', '/calling', '/integrations'],
  },
  {
    label:  'Automation',
    route:  '/autopilot',
    routes: ['/autopilot', '/reply-intel', '/api-keys', '/bulk-credits'],
  },
] as const;

export function TopNav() {
  const location = useLocation();
  const navigate  = useNavigate();

  function isActive(routes: readonly string[]) {
    return routes.includes(location.pathname);
  }

  return (
    <header className="h-12 bg-gray-950 border-b border-gray-800 flex items-center shrink-0">

      {/* Logo */}
      <div className="flex items-center px-4 h-full border-r border-gray-800 shrink-0">
        <img src={urapLogo} alt="URAP" className="h-8 w-auto" />
      </div>

      {/* Tabs — first 3 mirror Seamless.AI search modes; last 2 are URAP-specific */}
      <nav className="flex h-full ml-1 overflow-x-auto">
        {/* Visual separator before Engagement */}
        {NAV_TABS.flatMap((tab, i) => {
          const active = isActive(tab.routes);
          const btn = (
            <button
              key={tab.route}
              onClick={() => navigate(tab.route)}
              className={`relative px-4 h-full text-sm font-medium transition-colors whitespace-nowrap ${
                active ? 'text-white' : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              {tab.label}
              {active && (
                <span className="absolute bottom-0 left-3 right-3 h-0.5 bg-indigo-500 rounded-t-full" />
              )}
            </button>
          );
          return i === 3
            ? [<div key="sep" className="my-3 w-px bg-gray-800 mx-1 shrink-0" />, btn]
            : [btn];
        })}
      </nav>

      {/* Right actions */}
      <div className="ml-auto flex items-center gap-1.5 px-4 shrink-0">
        <button
          className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 text-xs text-gray-300
                     border border-gray-700 hover:border-gray-500 hover:text-white rounded
                     transition-colors"
          onClick={() => navigate('/integrations')}
        >
          🔗 Connect Email
        </button>
        <button
          className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 text-xs text-gray-300
                     border border-gray-700 hover:border-gray-500 hover:text-white rounded
                     transition-colors"
          onClick={() => navigate('/api-keys')}
        >
          &lt;/&gt; Get Embed
        </button>
        <button
          className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500
                     text-white text-xs font-semibold rounded transition-colors"
        >
          ↑ Upgrade
        </button>
        <button title="Notifications"
          className="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-white
                     hover:bg-gray-800 rounded transition-colors text-sm">🔔</button>
        <button title="Settings" onClick={() => navigate('/integrations')}
          className="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-white
                     hover:bg-gray-800 rounded transition-colors text-sm">⚙</button>
      </div>
    </header>
  );
}
