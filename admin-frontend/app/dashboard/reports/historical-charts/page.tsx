'use client';

import { useState } from 'react';
import PageHeader from '@/components/layout/PageHeader';
import { Card } from '@/components/ui/Card';
import { Table, TBody, Td, Th, THead, Tr } from '@/components/ui/Table';
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/States';
import { FormField, Input, Select } from '@/components/ui/Field';
import { useResults } from '@/hooks/useResults';
import { useMarketsLookup } from '@/hooks/useMarketsLookup';
import { Line, LineChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

export default function HistoricalChartsPage() {
  const { markets } = useMarketsLookup();
  const [marketId, setMarketId] = useState<number | ''>('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  const { data, isLoading, isError, error } = useResults({
    marketId: marketId || undefined,
    status: 'Published',
    dateFrom: dateFrom || undefined,
    dateTo: dateTo || undefined,
    limit: 100,
  });

  const rows = [...(data?.items ?? [])].sort((a, b) => a.date.localeCompare(b.date));
  const chartRows = rows.map((result) => ({
    date: result.date,
    openAnk: result.openAnk == null ? null : Number(result.openAnk),
    closeAnk: result.closeAnk == null ? null : Number(result.closeAnk),
    jodi: result.jodi == null ? null : Number(result.jodi),
  }));

  return (
    <div>
      <PageHeader icon="chart" title="Historical Charts" description="A panel-style chart of declared results over time, from our own data only." />
      <Card>
        <div className="grid grid-cols-1 gap-3 border-b border-slate-100 p-4 sm:grid-cols-3">
          <FormField label="Market">
            <Select required value={marketId} onChange={(e) => setMarketId(e.target.value ? Number(e.target.value) : '')}>
              <option value="">Select a market…</option>
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

        {!marketId && <EmptyState title="Select a market to view its chart" />}
        {marketId && isLoading && <LoadingState />}
        {marketId && isError && <ErrorState message={(error as Error).message} />}
        {marketId && !isLoading && rows.length === 0 && <EmptyState title="No published results in this range" />}

        {marketId && rows.length > 0 && (
          <>
          <div className="h-72 border-b border-slate-100 p-4">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartRows} margin={{ top: 8, right: 20, left: -20, bottom: 4 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} /><YAxis tick={{ fontSize: 11 }} />
                <Tooltip /><Legend />
                <Line type="monotone" dataKey="openAnk" name="Open Ank" stroke="#2563eb" connectNulls />
                <Line type="monotone" dataKey="closeAnk" name="Close Ank" stroke="#16a34a" connectNulls />
                <Line type="monotone" dataKey="jodi" name="Jodi" stroke="#9333ea" connectNulls />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <Table>
            <THead>
              <Tr>
                <Th>Date</Th>
                <Th>Open Panna</Th>
                <Th>Open Ank</Th>
                <Th>Jodi</Th>
                <Th>Close Ank</Th>
                <Th>Close Panna</Th>
              </Tr>
            </THead>
            <TBody>
              {rows.map((r) => (
                <Tr key={r.id}>
                  <Td className="font-medium text-slate-900">{r.date}</Td>
                  <Td className="font-mono">{r.openPanna ?? '—'}</Td>
                  <Td className="font-mono">{r.openAnk ?? '—'}</Td>
                  <Td className="font-mono font-bold">{r.jodi ?? '—'}</Td>
                  <Td className="font-mono">{r.closeAnk ?? '—'}</Td>
                  <Td className="font-mono">{r.closePanna ?? '—'}</Td>
                </Tr>
              ))}
            </TBody>
          </Table>
          </>
        )}
      </Card>
    </div>
  );
}
