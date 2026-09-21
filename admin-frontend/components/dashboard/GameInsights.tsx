'use client';

import { useState } from 'react';
import { Card, CardBody, CardHeader, CardTitle } from '@/components/ui/Card';
import { Table, TBody, Td, Th, THead, Tr } from '@/components/ui/Table';
import { LoadingState, EmptyState } from '@/components/ui/States';
import { FormField, Select } from '@/components/ui/Field';
import Badge from '@/components/ui/Badge';
import { useGameStatistics, useNumberFrequency } from '@/hooks/useReports';
import { useGameTypes } from '@/hooks/useGameTypes';
import { useMarketsLookup } from '@/hooks/useMarketsLookup';

const GAME_TONE: Record<string, 'blue' | 'purple' | 'amber' | 'green' | 'slate'> = {
  SINGLE: 'blue',
  JODI: 'purple',
  SINGLE_PANNA: 'amber',
  DOUBLE_PANNA: 'amber',
  TRIPLE_PANNA: 'amber',
  HALF_SANGAM: 'green',
  FULL_SANGAM: 'green',
};

export default function GameInsights() {
  const { data: gameStats, isLoading: statsLoading } = useGameStatistics();
  const { data: gameTypes } = useGameTypes();
  const { markets } = useMarketsLookup();

  const [gameType, setGameType] = useState('');
  const [marketId, setMarketId] = useState<number | ''>('');
  const { data: frequency, isLoading: freqLoading } = useNumberFrequency({
    gameType: gameType || undefined,
    marketId: marketId || undefined,
    limit: 10,
  });

  const maxCount = frequency && frequency.length > 0 ? frequency[0].count : 1;

  return (
    <div className="mb-6 grid gap-4 xl:grid-cols-5">
      <Card className="xl:col-span-2">
        <CardHeader>
          <CardTitle subtitle="Credits staked, wins, payouts, and net by game type">Game Statistics</CardTitle>
        </CardHeader>
        {statsLoading && <LoadingState />}
        {gameStats && gameStats.length === 0 && <EmptyState title="No simulations yet" />}
        {gameStats && gameStats.length > 0 && (
          <Table>
            <THead>
              <Tr>
                <Th>Game</Th>
                <Th>Staked</Th>
                <Th>Wins</Th>
                <Th>Net</Th>
              </Tr>
            </THead>
            <TBody>
              {gameStats.map((row) => (
                <Tr key={row.gameType}>
                  <Td>
                    <Badge tone={GAME_TONE[row.gameType] ?? 'slate'}>{row.gameType.replace('_', ' ')}</Badge>
                  </Td>
                  <Td className="font-medium text-slate-900">{row.sales.toLocaleString()}</Td>
                  <Td>{row.winners}</Td>
                  <Td className={row.profit >= 0 ? 'font-semibold text-emerald-600' : 'font-semibold text-red-600'}>
                    {row.profit.toLocaleString()}
                  </Td>
                </Tr>
              ))}
            </TBody>
          </Table>
        )}
      </Card>

      <Card className="xl:col-span-3">
        <CardHeader>
          <CardTitle subtitle="Most-selected numbers — pick a game and/or market to drill in">Hot Numbers</CardTitle>
        </CardHeader>
        <div className="grid grid-cols-2 gap-3 border-b border-slate-100 px-5 py-3">
          <FormField label="Game type">
            <Select value={gameType} onChange={(e) => setGameType(e.target.value)}>
              <option value="">All game types</option>
              {gameTypes?.map((gt) => (
                <option key={gt.id} value={gt.code}>
                  {gt.code.replace('_', ' ')}
                </option>
              ))}
            </Select>
          </FormField>
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
        </div>
        <CardBody>
          {freqLoading && <LoadingState />}
          {frequency && frequency.length === 0 && <EmptyState title="No selections for this filter yet" />}
          {frequency && frequency.length > 0 && (
            <div className="space-y-2">
              {frequency.map((row, i) => (
                <div key={row.selection} className="flex items-center gap-3">
                  <span className="w-5 shrink-0 text-xs font-semibold text-slate-400">{i + 1}</span>
                  <span className="w-16 shrink-0 font-mono text-sm font-bold text-slate-900">{row.selection}</span>
                  <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-brand-400 to-brand-600"
                      style={{ width: `${Math.max(6, (row.count / maxCount) * 100)}%` }}
                    />
                  </div>
                  <span className="w-10 shrink-0 text-right text-xs font-semibold text-slate-500">{row.count}</span>
                </div>
              ))}
            </div>
          )}
        </CardBody>
      </Card>
    </div>
  );
}
