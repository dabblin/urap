import { NavLink } from 'react-router-dom';

const TABS = [
  { label: 'Contacts',  icon: '🔍', route: '/prospector' },
  { label: 'Companies', icon: '🏢', route: '/companies'  },
  { label: 'Agent',     icon: '⚡', route: '/warp-mode'  },
  { label: 'Email',     icon: '✉',  route: '/emailing'   },
  { label: 'Auto',      icon: '🤖', route: '/autopilot'  },
];

export function MobileBottomNav() {
  return (
    <nav
      className="md:hidden fixed bottom-0 inset-x-0 z-40
                 bg-gray-900/95 backdrop-blur border-t border-gray-800 flex"
      style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}
    >
      {TABS.map(tab => (
        <NavLink
          key={tab.route}
          to={tab.route}
          className={({ isActive }) =>
            `flex-1 flex flex-col items-center justify-center py-2 gap-0.5 min-h-[52px]
             transition-colors ${isActive ? 'text-indigo-400' : 'text-gray-500 active:text-gray-300'}`
          }
        >
          <span className="text-lg leading-none">{tab.icon}</span>
          <span className="text-[9px] font-medium uppercase tracking-wide">{tab.label}</span>
        </NavLink>
      ))}
    </nav>
  );
}
