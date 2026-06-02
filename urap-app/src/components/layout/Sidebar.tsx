import { NavLink } from 'react-router-dom';
import { getToolsByPillar } from '../../registry.js';

type Pillar = 'data' | 'engagement' | 'automation';

const PILLARS: Pillar[] = ['data', 'engagement', 'automation'];

export function Sidebar() {
  return (
    <aside
      className="hidden md:flex w-[52px] bg-gray-900 border-r border-gray-800 flex-col h-full
                 py-2 shrink-0 overflow-y-auto overflow-x-hidden"
    >
      {PILLARS.map((pillar, idx) => {
        const tools = getToolsByPillar(pillar);
        if (tools.length === 0) return null;
        return (
          <div key={pillar} className="flex flex-col items-center w-full">
            {/* Pillar divider — no text labels, matches Seamless.AI icon rail */}
            {idx > 0 && (
              <div className="w-7 h-px bg-gray-800 my-2" />
            )}

            {tools.map(tool => (
              <NavLink
                key={tool.id}
                to={tool.route}
                title={tool.label}
                className={({ isActive }) =>
                  `flex items-center justify-center w-9 h-9 rounded-xl mb-0.5
                   text-[18px] leading-none transition-all select-none ${
                     isActive
                       ? 'bg-indigo-600 text-white shadow shadow-indigo-500/30'
                       : 'text-gray-500 hover:bg-gray-800 hover:text-gray-200'
                   }`
                }
              >
                {tool.icon}
              </NavLink>
            ))}
          </div>
        );
      })}
    </aside>
  );
}
