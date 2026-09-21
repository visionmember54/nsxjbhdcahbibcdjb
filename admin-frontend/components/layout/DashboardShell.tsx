'use client';

import { useEffect, useRef, useState } from 'react';
import { useLogout } from '@/hooks/useAuth';
import Sidebar from './Sidebar';
import Topbar from './Topbar';
import NavigationMenu from './NavigationMenu';
import DashboardFooter from './DashboardFooter';

const COLLAPSE_STORAGE_KEY = 'kalyan_admin_sidebar_collapsed';
const IDLE_LIMIT_MS = 30 * 60 * 1000;

export default function DashboardShell({ children }: { children: React.ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const logout = useLogout();
  const logoutRef = useRef(logout.mutate);
  logoutRef.current = logout.mutate;

  // Sign out after 30 minutes without input (shared/unattended machines).
  useEffect(() => {
    let timer = setTimeout(() => logoutRef.current(), IDLE_LIMIT_MS);
    const reset = () => {
      clearTimeout(timer);
      timer = setTimeout(() => logoutRef.current(), IDLE_LIMIT_MS);
    };
    const events = ['pointerdown', 'keydown', 'scroll'] as const;
    events.forEach((e) => window.addEventListener(e, reset, { passive: true }));
    return () => {
      clearTimeout(timer);
      events.forEach((e) => window.removeEventListener(e, reset));
    };
  }, []);

  // Escape closes the mobile drawer.
  useEffect(() => {
    if (!mobileOpen) return;
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setMobileOpen(false);
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [mobileOpen]);

  // Restore the desktop sidebar's collapsed/expanded preference across visits.
  useEffect(() => {
    setCollapsed(localStorage.getItem(COLLAPSE_STORAGE_KEY) === '1');
  }, []);

  function toggleCollapsed() {
    setCollapsed((prev) => {
      const next = !prev;
      localStorage.setItem(COLLAPSE_STORAGE_KEY, next ? '1' : '0');
      return next;
    });
  }

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-[70] focus:rounded-lg focus:bg-white focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-brand-700 focus:shadow-lg"
      >
        Skip to content
      </a>
      <Sidebar collapsed={collapsed} onToggleCollapsed={toggleCollapsed} />

      {mobileOpen && (
        <div className="fixed inset-0 z-40 flex lg:hidden" role="dialog" aria-modal="true" aria-label="Navigation menu">
          <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm" onClick={() => setMobileOpen(false)} />
          <div className="relative flex h-full w-72 flex-col overflow-hidden bg-sidebar-gradient shadow-2xl">
            <div className="flex items-center justify-between border-b border-white/10 px-4 py-3.5">
              <div className="flex items-center gap-2.5">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-brand-400 to-brand-600 text-xs font-bold text-white shadow-glow">
                  K
                </div>
                <span className="text-sm font-bold text-white">Kalyan Admin</span>
              </div>
              <button onClick={() => setMobileOpen(false)} className="rounded-md p-1.5 text-slate-400 hover:bg-white/10 hover:text-white" aria-label="Close menu">
                <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
                </svg>
              </button>
            </div>
            <NavigationMenu onNavigate={() => setMobileOpen(false)} />
          </div>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <Topbar onMenuClick={() => setMobileOpen(true)} />
        <main id="main-content" tabIndex={-1} className="flex flex-1 flex-col overflow-y-auto overflow-x-hidden">
          <div className="flex-1 p-4 sm:p-5 lg:p-8">{children}</div>
          <DashboardFooter />
        </main>
      </div>
    </div>
  );
}
