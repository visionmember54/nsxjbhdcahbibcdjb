'use client';

import { useState } from 'react';
import PageHeader from '@/components/layout/PageHeader';
import { Card } from '@/components/ui/Card';
import { FormField, Input, Select } from '@/components/ui/Field';
import Pagination from '@/components/ui/Pagination';
import ResultsTable from '@/components/results/ResultsTable';
import { useResults } from '@/hooks/useResults';
import { useMarketsLookup } from '@/hooks/useMarketsLookup';

export default function HistoricalResultsPage() {
  const { markets } = useMarketsLookup();
  const [marketId, setMarketId] = useState<number | ''>('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [offset, setOffset] = useState(0);
  const limit = 20;

  const { data, isLoading, isError, error } = useResults({
    marketId: marketId || undefined,
    dateFrom: dateFrom || undefined,
    dateTo: dateTo || undefined,
    limit,
    offset,
  });

  return (
    <div>
      <PageHeader icon="check" title="Historical Results" description="Published and corrected results, filterable by market and date range." />
      <Card>
        <div className="grid grid-cols-1 gap-3 border-b border-slate-100 p-4 sm:grid-cols-3">
          <FormField label="Market">
            <Select value={marketId} onChange={(e) => setMarketId(e.target.value ? Number(e.target.value) : '')}>
              <option value="">All markets</option>
              {markets.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name}
                </option>
              ))}
            </Select>
          </FormField>
          <FormField label="From">
            <Input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
          </FormField>
          <FormField label="To">
            <Input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
          </FormField>
        </div>

        <ResultsTable
          results={data?.items.filter((r) => r.status !== 'Draft')}
          isLoading={isLoading}
          isError={isError}
          errorMessage={(error as Error)?.message}
        />
        {data && <Pagination total={data.total} limit={limit} offset={offset} onOffsetChange={setOffset} />}
      </Card>
    </div>
  );
}
