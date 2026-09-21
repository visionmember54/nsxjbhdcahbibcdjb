'use client';

import { useState } from 'react';
import PageHeader from '@/components/layout/PageHeader';
import { Card } from '@/components/ui/Card';
import { Table, TBody, Td, Th, THead, Tr } from '@/components/ui/Table';
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/States';
import { FormField, Select } from '@/components/ui/Field';
import { useNumberFrequency } from '@/hooks/useReports';
import { useMarketsLookup } from '@/hooks/useMarketsLookup';
import { useGameTypes } from '@/hooks/useGameTypes';

export default function NumberFrequencyPage() {
  const { markets } = useMarketsLookup();
  const { data: gameTypes } = useGameTypes();
  const [marketId, setMarketId] = useState<number | ''>('');
  const [gameType, setGameType] = useState('');

  const { data, isLoading, isError, error } = useNumberFrequency({ marketId: marketId || undefined, gameType: gameType || undefined, limit: 30 });

  return (
    <div>
      <PageHeader icon="chart" title="Number Frequency" description="Most frequently selected numbers, most selected first." />
      <Card>
        <div className="grid grid-cols-1 gap-3 border-b border-slate-100 p-4 sm:grid-cols-2">
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
          <FormField label="Game type">
            <Select value={gameType} onChange={(e) => setGameType(e.target.value)}>
              <option value="">All game types</option>
              {gameTypes?.map((gt) => (
                <option key={gt.id} value={gt.code}>
                  {gt.code}
                </option>
              ))}
            </Select>
          </FormField>
        </div>

        {isLoading && <LoadingState />}
        {isError && <ErrorState message={(error as Error).message} />}
        {data && data.length === 0 && <EmptyState title="No selections yet" />}

        {data && data.length > 0 && (
          <Table>
            <THead>
              <Tr>
                <Th>Selection</Th>
                <Th>Times chosen</Th>
              </Tr>
            </THead>
            <TBody>
              {data.map((row) => (
                <Tr key={row.selection}>
                  <Td className="font-mono font-medium text-slate-900">{row.selection}</Td>
                  <Td>{row.count}</Td>
                </Tr>
              ))}
            </TBody>
          </Table>
        )}
      </Card>
    </div>
  );
}
