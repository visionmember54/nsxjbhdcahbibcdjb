'use client';

import NavigationMenu from './NavigationMenu';

function HamburgerIcon() {
  return (
    <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
      <path fillRule="evenodd" d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
    </svg>
  );
}

function CrossIcon() {
  return (
    <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
      <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
    </svg>
  );
}

export default function Sidebar({
  collapsed,
  onToggleCollapsed,
}: {
  collapsed: boolean;
  onToggleCollapsed: () => void;
}) {
  return (
    <aside
      className={`hidden h-screen shrink-0 flex-col bg-sidebar-gradient transition-[width] duration-200 lg:flex ${
        collapsed ? 'w-[76px]' : 'w-72'
      }`}
    >
      <div className={`flex h-16 items-center border-b border-white/10 ${collapsed ? 'justify-center px-2' : 'justify-between px-5'}`}>
        {!collapsed && (
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-brand-400 to-brand-600 text-sm font-bold text-white shadow-glow">
              K
            </div>
            <div>
              <p className="text-sm font-bold leading-tight text-white">Kalyan Admin</p>
              <p className="mt-0.5 text-[11px] font-medium uppercase tracking-wide text-slate-500">Operations Console</p>
            </div>
          </div>
        )}
        <button
          onClick={onToggleCollapsed}
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-white/10 hover:text-white"
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <HamburgerIcon /> : <CrossIcon />}
        </button>
      </div>

      <NavigationMenu collapsed={collapsed} />

      {!collapsed && (
        <div className="border-t border-white/10 px-5 py-3 text-[11px] leading-relaxed text-slate-500">
          Educational simulator. Virtual credits only.
        </div>
      )}
    </aside>
  );
}
