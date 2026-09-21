'use client';

import { useMemo, useState } from 'react';
import PageHeader from '@/components/layout/PageHeader';
import { Card } from '@/components/ui/Card';
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/States';
import { FormField, Input, Select } from '@/components/ui/Field';
import Badge from '@/components/ui/Badge';
import { useResults } from '@/hooks/useResults';
import { useMarketsLookup } from '@/hooks/useMarketsLookup';
import { daysAgoLocalIso, todayLocalIso } from '@/lib/date';
import type { MarketResult } from '@/lib/api/types';

const CATEGORY_TONE: Record<string, 'green' | 'blue' | 'amber' | 'purple' | 'slate'> = {
  MATKA: 'green',
  STARLINE: 'blue',
  GALI_DISAWAR: 'amber',
  CUSTOM: 'purple',
};

function formatCell(result: MarketResult | undefined, category: string): string {
  const isSingleDraw = category === 'STARLINE' || category === 'GALI_DISAWAR';
  if (!result) return isSingleDraw ? '**' : '***-**-***';
  if (isSingleDraw) return result.singleResult ?? result.openAnk ?? '**';
  const open = result.openPanna ?? '***';
  const jodi = result.jodi ?? '**';
  const close = result.closePanna ?? '***';
  return `${open}-${jodi}-${close}`;
}

export default function PanelChartPage() {
  const { markets } = useMarketsLookup();
  const [dateFrom, setDateFrom] = useState(daysAgoLocalIso(13));
  const [dateTo, setDateTo] = useState(todayLocalIso());
  const [category, setCategory] = useState('');

  // 200 is the backend's hard cap (see PageParams) -- comfortably covers the
  // default 14-day range across all current markets. A truncation notice
  // below tells the admin to narrow the range if a wider query hits it.
  const { data, isLoading, isError, error } = useResults({
    status: 'Published',
    dateFrom,
    dateTo,
    limit: 200,
  });

  const visibleMarkets = useMemo(
    () =>
      [...markets]
        .filter((m) => !category || m.category === category)
        .sort((a, b) => a.category.localeCompare(b.category) || a.display_order - b.display_order || a.name.localeCompare(b.name)),
    [markets, category]
  );

  const { dates, grid } = useMemo(() => {
    // Panel chart shows main market-level draws only (slotId === null) --
    // Starline's per-slot hourly detail lives on its own slot-level chart.
    const rows = (data?.items ?? []).filter((r) => r.slotId === null);
    const map = new Map<string, Map<number, MarketResult>>();
    for (const r of rows) {
      if (!map.has(r.date)) map.set(r.date, new Map());
      map.get(r.date)!.set(r.marketId, r);
    }
    const allDates = Array.from(map.keys()).sort().reverse();
    return { dates: allDates, grid: map };
  }, [data]);

  return (
    <div>
      <PageHeader
        icon="chart"
        title="Panel Chart"
        description="Every market's declared numbers, by date — Milan Day, Milan Night, Rajdhani, Kalyan, and all others, side by side."
      />

      <Card>
        <div className="grid grid-cols-1 gap-3 border-b border-slate-100 p-4 sm:grid-cols-3">
          <FormField label="From">
            <Input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
          </FormField>
          <FormField label="To">
            <Input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
          </FormField>
          <FormField label="Category">
            <Select value={category} onChange={(e) => setCategory(e.target.value)}>
              <option value="">All categories</option>
              <option value="MATKA">Main / Matka</option>
              <option value="STARLINE">Starline</option>
              <option value="GALI_DISAWAR">Gali–Disawar</option>
              <option value="CUSTOM">Custom</option>
            </Select>
          </FormField>
        </div>

        {isLoading && <LoadingState />}
        {isError && <ErrorState message={(error as Error).message} />}
        {data && data.total > data.items.length && (
          <p className="border-b border-amber-100 bg-amber-50 px-4 py-2 text-xs font-medium text-amber-700">
            Showing the most recent {data.items.length} of {data.total} published results — narrow the date range to see everything.
          </p>
        )}
        {!isLoading && !isError && visibleMarkets.length === 0 && <EmptyState title="No markets in this category" />}
        {!isLoading && !isError && visibleMarkets.length > 0 && dates.length === 0 && (
          <EmptyState title="No published results in this range" hint="Try widening the date range, or publish a result first." />
        )}

        {!isLoading && !isError && dates.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full min-w-max border-separate border-spacing-0 text-left text-sm">
              <thead>
                <tr className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                  <th className="sticky left-0 z-10 border-b border-r border-slate-200 bg-slate-50/95 px-4 py-3 backdrop-blur">
                    Date
                  </th>
                  {visibleMarkets.map((m) => (
                    <th key={m.id} className="whitespace-nowrap border-b border-slate-200 bg-slate-50/80 px-4 py-3">
                      <div className="flex flex-col gap-1">
                        <span className="text-slate-800">{m.name}</span>
                        <Badge tone={CATEGORY_TONE[m.category] ?? 'slate'}>{m.category.replace('_', '–')}</Badge>
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {dates.map((date, i) => (
                  <tr key={date} className={`transition-colors hover:bg-brand-50/40 ${i % 2 === 1 ? 'bg-slate-50/40' : ''}`}>
                    <td className="sticky left-0 z-10 whitespace-nowrap border-r border-b border-slate-100 bg-white px-4 py-3 font-semibold text-slate-900">
                      {date}
                    </td>
                    {visibleMarkets.map((m) => {
                      const result = grid.get(date)?.get(m.id);
                      const cell = formatCell(result, m.category);
                      const hasResult = !!result;
                      return (
                        <td key={m.id} className="whitespace-nowrap border-b border-slate-100 px-4 py-3">
                          <span
                            className={`font-mono text-[13px] font-bold tracking-wide ${
                              hasResult ? 'text-brand-700' : 'text-slate-300'
                            }`}
                          >
                            {cell}
                          </span>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
