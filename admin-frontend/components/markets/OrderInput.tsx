'use client';

import { useEffect, useState } from 'react';

/** Inline-editable display-order number, saved on blur/Enter with no modal --
 * shared by the markets table (main-screen sequence) and anywhere else a
 * display_order needs setting straight from a table row. */
export default function OrderInput({
  value,
  onSave,
  pending,
}: {
  value: number;
  onSave: (next: number) => void;
  pending?: boolean;
}) {
  const [draft, setDraft] = useState(String(value));
  const [justSaved, setJustSaved] = useState(false);

  useEffect(() => {
    setDraft(String(value));
  }, [value]);

  function commit() {
    const next = Number(draft);
    if (!Number.isFinite(next) || next === value) {
      setDraft(String(value));
      return;
    }
    onSave(next);
    setJustSaved(true);
    setTimeout(() => setJustSaved(false), 1200);
  }

  return (
    <div className="flex items-center gap-1.5">
      <input
        type="number"
        value={draft}
        disabled={pending}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={commit}
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            e.preventDefault();
            (e.target as HTMLInputElement).blur();
          }
        }}
        className="w-14 rounded-md border border-slate-300 bg-white px-2 py-1 text-center text-sm font-medium text-slate-800 shadow-sm transition-colors focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-100 disabled:opacity-50"
        aria-label="Display order"
      />
      {pending && (
        <svg className="h-3.5 w-3.5 animate-spin text-brand-500" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
        </svg>
      )}
      {!pending && justSaved && (
        <svg className="h-3.5 w-3.5 text-emerald-500" viewBox="0 0 20 20" fill="currentColor">
          <path
            fillRule="evenodd"
            d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 111.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z"
            clipRule="evenodd"
          />
        </svg>
      )}
    </div>
  );
}
