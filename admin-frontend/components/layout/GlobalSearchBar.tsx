'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useGlobalSearch } from '@/hooks/useGlobalSearch';
import { Icon } from './icons';

const STATUS_TONE: Record<string, string> = {
  Won: 'text-emerald-600',
  Lost: 'text-red-600',
  Pending: 'text-amber-600',
};

export default function GlobalSearchBar() {
  const router = useRouter();
  const [input, setInput] = useState('');
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Debounced -- don't hit /admin/search on every keystroke.
  useEffect(() => {
    const id = setTimeout(() => setQuery(input), 250);
    return () => clearTimeout(id);
  }, [input]);

  const { data, isFetching } = useGlobalSearch(query);

  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setOpen(false);
    document.addEventListener('click', onClick);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('click', onClick);
      document.removeEventListener('keydown', onKey);
    };
  }, []);

  function go(path: string) {
    setOpen(false);
    setInput('');
    router.push(path);
  }

  const hasResults = !!data && (data.users.length > 0 || data.markets.length > 0 || !!data.bid);
  const showPanel = open && query.length > 0;

  return (
    <div ref={containerRef} className="relative hidden w-full max-w-sm sm:block">
      <div className="relative">
        <span className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400">
          <Icon name="search" className="h-4 w-4" />
        </span>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onFocus={() => setOpen(true)}
          placeholder="Search users, markets, bid id…"
          className="w-full rounded-lg border border-slate-200 bg-white py-1.5 pl-9 pr-3 text-xs font-medium text-slate-700 shadow-soft placeholder:text-slate-400 focus:border-brand-300 focus:outline-none focus:ring-2 focus:ring-brand-100"
        />
      </div>

      {showPanel && (
        <div className="absolute left-0 right-0 z-40 mt-2 max-h-96 overflow-y-auto rounded-xl border border-slate-200 bg-white p-1.5 shadow-card ring-1 ring-slate-900/5">
          {isFetching && <p className="px-3 py-2 text-xs text-slate-400">Searching…</p>}

          {!isFetching && !hasResults && <p className="px-3 py-2 text-xs text-slate-400">No matches for &ldquo;{query}&rdquo;.</p>}

          {!!data?.bid && (
            <div className="mb-1 border-b border-slate-100 pb-1">
              <p className="px-3 py-1 text-[10px] font-bold uppercase tracking-wide text-slate-400">Bid #{data.bid.id}</p>
              <button
                onClick={() => go(`/dashboard/students/${data.bid!.userId}`)}
                className="block w-full rounded-lg px-3 py-2 text-left text-xs transition-colors hover:bg-brand-50"
              >
                <span className="font-semibold text-slate-800">{data.bid.userName ?? `User #${data.bid.userId}`}</span>
                <span className="text-slate-500"> bet {data.bid.selection} on {data.bid.marketName ?? `market #${data.bid.marketId}`}</span>
                <span className={`ml-1 font-semibold ${STATUS_TONE[data.bid.status] ?? 'text-slate-500'}`}>({data.bid.status})</span>
              </button>
            </div>
          )}

          {!!data?.users.length && (
            <div className="mb-1 border-b border-slate-100 pb-1">
              <p className="px-3 py-1 text-[10px] font-bold uppercase tracking-wide text-slate-400">Users</p>
              {data.users.map((u) => (
                <button
                  key={u.id}
                  onClick={() => go(`/dashboard/students/${u.id}`)}
                  className="block w-full rounded-lg px-3 py-2 text-left text-xs transition-colors hover:bg-brand-50"
                >
                  <span className="font-semibold text-slate-800">{u.name}</span>
                  <span className="ml-1.5 text-slate-500">{u.phone}</span>
                </button>
              ))}
            </div>
          )}

          {!!data?.markets.length && (
            <div>
              <p className="px-3 py-1 text-[10px] font-bold uppercase tracking-wide text-slate-400">Markets</p>
              {data.markets.map((m) => (
                <button
                  key={m.id}
                  onClick={() => go(`/dashboard/markets/${m.id}`)}
                  className="block w-full rounded-lg px-3 py-2 text-left text-xs transition-colors hover:bg-brand-50"
                >
                  <span className="font-semibold text-slate-800">{m.name}</span>
                  <span className="ml-1.5 text-slate-500">{m.category}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
