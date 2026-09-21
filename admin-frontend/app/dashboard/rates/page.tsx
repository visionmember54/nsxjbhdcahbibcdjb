'use client';

import { useState } from 'react';
import PageHeader from '@/components/layout/PageHeader';
import { Card } from '@/components/ui/Card';
import { Table, TBody, Td, Th, THead, Tr } from '@/components/ui/Table';
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/States';
import Badge from '@/components/ui/Badge';
import { FormField, Select } from '@/components/ui/Field';
import { useRates, useUpdateRateStatus } from '@/hooks/useRates';
import { useMarketsLookup } from '@/hooks/useMarketsLookup';

export default function SimulatedRatesPage() {
  const { markets, byId } = useMarketsLookup();
  const [marketId, setMarketId] = useState<number | ''>('');
  const { data: rates, isLoading, isError, error } = useRates(marketId || null);
  const updateStatus = useUpdateRateStatus();

  return (
    <div>
      <PageHeader
        icon="percent"
        title="Simulated Rates"
        description="Win per 10 credits staked, time-versioned via effective_from. The 'current' rate is the latest already-effective Active row."
      />
      <Card>
        <div className="border-b border-slate-100 p-4">
          <FormField label="Filter by market">
            <Select value={marketId} onChange={(e) => setMarketId(e.target.value ? Number(e.target.value) : '')} className="max-w-xs">
              <option value="">All markets</option>
              {markets.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name}
                </option>
              ))}
            </Select>
          </FormField>
        </div>

        {isLoading && <LoadingState />}
        {isError && <ErrorState message={(error as Error).message} />}
        {rates && rates.length === 0 && <EmptyState title="No rates configured yet" />}

        {rates && rates.length > 0 && (
          <Table>
            <THead>
              <Tr>
                <Th>Market</Th>
                <Th>Slot</Th>
                <Th>Game Type</Th>
                <Th>Rate</Th>
                <Th>Effective from</Th>
                <Th>Status</Th>
                <Th></Th>
              </Tr>
            </THead>
            <TBody>
              {rates.map((r) => (
                <Tr key={r.id}>
                  <Td className="font-medium text-slate-900">{byId.get(r.market_id)?.name ?? `#${r.market_id}`}</Td>
                  <Td>{r.slot_id ?? '—'}</Td>
                  <Td>{r.game_type_code}</Td>
                  <Td>{r.rate}</Td>
                  <Td>{r.effective_from}</Td>
                  <Td>
                    <Badge tone={r.status === 'Active' ? 'green' : 'slate'}>{r.status}</Badge>
                  </Td>
                  <Td>
                    <button
                      className="text-xs font-semibold text-brand-600 hover:underline"
                      onClick={() => updateStatus.mutate({ id: r.id, status: r.status === 'Active' ? 'Inactive' : 'Active' })}
                    >
                      {r.status === 'Active' ? 'Deactivate' : 'Activate'}
                    </button>
                  </Td>
                </Tr>
              ))}
            </TBody>
          </Table>
        )}
      </Card>
      <p className="mt-3 text-xs text-slate-400">
        To add a new rate for a market, open that market from the Markets section — rates are configured alongside its game types.
      </p>
    </div>
  );
}
