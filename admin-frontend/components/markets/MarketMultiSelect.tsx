'use client';

import { useMemo } from 'react';
import { Checkbox } from '@/components/ui/Field';
import type { Market } from '@/lib/api/types';

/** Grouped by category with a per-category "select all" -- the whole point
 * is applying one rate or one game-type config across every market in a
 * category (e.g. all of Gali-Disawar) in a single submission, instead of
 * ticking each market by hand. */
export default function MarketMultiSelect({
  markets,
  selected,
  onChange,
}: {
  markets: Market[];
  selected: Set<number>;
  onChange: (next: Set<number>) => void;
}) {
  const groups = useMemo(() => {
    const bySlug = new Map<string, Market[]>();
    for (const m of markets) {
      const list = bySlug.get(m.category) ?? [];
      list.push(m);
      bySlug.set(m.category, list);
    }
    return Array.from(bySlug.entries());
  }, [markets]);

  function toggle(id: number) {
    const next = new Set(selected);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    onChange(next);
  }

  function toggleGroup(group: Market[], allSelected: boolean) {
    const next = new Set(selected);
    for (const m of group) {
      if (allSelected) next.delete(m.id);
      else next.add(m.id);
    }
    onChange(next);
  }

  return (
    <div className="max-h-64 space-y-3 overflow-y-auto rounded-md border border-slate-200 p-3">
      {groups.map(([category, group]) => {
        const allSelected = group.every((m) => selected.has(m.id));
        return (
          <div key={category}>
            <div className="mb-1 flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wide text-slate-500">{category}</span>
              <button
                type="button"
                className="text-xs font-semibold text-brand-600 hover:underline"
                onClick={() => toggleGroup(group, allSelected)}
              >
                {allSelected ? 'Clear' : 'Select all'}
              </button>
            </div>
            <div className="space-y-1">
              {group.map((m) => (
                <Checkbox key={m.id} label={m.name} checked={selected.has(m.id)} onChange={() => toggle(m.id)} />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
