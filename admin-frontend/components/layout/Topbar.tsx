'use client';

import Link from 'next/link';
import { useEffect } from 'react';
import { useCurrentAdmin, useLogout } from '@/hooks/useAuth';
import Badge from '@/components/ui/Badge';

export default function Topbar({ onMenuClick }: { onMenuClick: () => void }) {
  const { data: admin } = useCurrentAdmin();
  const logout = useLogout();

  // <details> menus: close on outside click, Escape, or choosing an item.
  useEffect(() => {
    const closeAll = (except?: Element | null) =>
      document.querySelectorAll<HTMLDetailsElement>('header details[open]').forEach((d) => d !== except && d.removeAttribute('open'));
    const onClick = (e: MouseEvent) => {
      const t = e.target as HTMLElement;
      closeAll(t.closest('details'));
      if (t.closest('details a')) closeAll();
    };
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && closeAll();
    document.addEventListener('click', onClick);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('click', onClick);
      document.removeEventListener('keydown', onKey);
    };
  }, []);

  return (
    <header className="sticky top-0 z-30 flex items-center justify-between border-b border-slate-200/80 bg-white/80 px-4 py-3 shadow-soft backdrop-blur-md lg:px-8">
      <button onClick={onMenuClick} className="rounded-lg p-2 text-slate-500 transition-colors hover:bg-slate-100 lg:hidden" aria-label="Open menu">
        <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
        </svg>
      </button>

      <p className="hidden text-xs font-semibold uppercase tracking-wide text-slate-400 lg:block">Operations Console</p>

      <div className="flex items-center gap-3">
        <details className="group relative hidden sm:block">
          <summary className="flex cursor-pointer list-none items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 shadow-soft transition-colors hover:border-brand-200 hover:bg-brand-50/60 hover:text-brand-800 [&::-webkit-details-marker]:hidden">
            Quick actions
            <span aria-hidden="true" className="text-slate-400 transition-transform group-open:rotate-180">⌄</span>
          </summary>
          <div className="absolute right-0 z-40 mt-2 w-56 rounded-xl border border-slate-200 bg-white p-1.5 shadow-card ring-1 ring-slate-900/5">
            <Link href="/dashboard/results/publish" className="block rounded-lg px-3 py-2 text-xs font-semibold text-slate-700 transition-colors hover:bg-brand-50 hover:text-brand-800">Publish a result</Link>
            <Link href="/dashboard/markets" className="block rounded-lg px-3 py-2 text-xs font-semibold text-slate-700 transition-colors hover:bg-brand-50 hover:text-brand-800">Manage markets</Link>
            <Link href="/dashboard/students" className="block rounded-lg px-3 py-2 text-xs font-semibold text-slate-700 transition-colors hover:bg-brand-50 hover:text-brand-800">Manage users</Link>
          </div>
        </details>
        {admin && (
          <details className="group relative">
            <summary className="flex cursor-pointer list-none items-center gap-2.5 rounded-lg py-1 pl-1 pr-2 transition-colors hover:bg-slate-100 [&::-webkit-details-marker]:hidden">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-brand-400 to-brand-600 text-xs font-bold text-white shadow-sm">
                {admin.name.slice(0, 1).toUpperCase()}
              </div>
              <div className="hidden text-left sm:block">
                <p className="text-xs font-semibold leading-tight text-slate-800">{admin.name}</p>
                <Badge tone={admin.role === 'super_admin' ? 'purple' : 'blue'}>{admin.role}</Badge>
              </div>
              <span aria-hidden="true" className="text-sm text-slate-400 transition-transform group-open:rotate-180">⌄</span>
            </summary>
            <div className="absolute right-0 z-40 mt-2 w-56 rounded-xl border border-slate-200 bg-white p-1.5 shadow-card ring-1 ring-slate-900/5">
              <div className="border-b border-slate-100 px-3 py-2">
                <p className="truncate text-xs font-semibold text-slate-800">{admin.email}</p>
                <p className="mt-0.5 text-xs capitalize text-slate-500">{admin.role.replace('_', ' ')}</p>
              </div>
              <button onClick={() => logout.mutate()} className="mt-1 w-full rounded-lg px-3 py-2 text-left text-xs font-semibold text-red-600 transition-colors hover:bg-red-50">
                Sign out
              </button>
            </div>
          </details>
        )}
      </div>
    </header>
  );
}
