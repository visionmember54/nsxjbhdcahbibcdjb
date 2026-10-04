'use client';

import { useState } from 'react';
import PageHeader from '@/components/layout/PageHeader';
import { Card } from '@/components/ui/Card';
import { Table, TBody, Td, Th, THead, Tr } from '@/components/ui/Table';
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/States';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';
import { FormField, Input, Select } from '@/components/ui/Field';
import { useRates, useUpdateRateStatus, useCreateRateBulk } from '@/hooks/useRates';
import { useGameTypes } from '@/hooks/useGameTypes';
import { useMarketsLookup } from '@/hooks/useMarketsLookup';
import MarketMultiSelect from '@/components/markets/MarketMultiSelect';
import { todayLocalIso } from '@/lib/date';

function BulkSetRateModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { markets } = useMarketsLookup();
  const { data: gameTypes } = useGameTypes();
  const bulkCreate = useCreateRateBulk();
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [gameTypeId, setGameTypeId] = useState<number | ''>('');
  const [rate, setRate] = useState('');
  const [effectiveFrom, setEffectiveFrom] = useState(todayLocalIso());

  return (
    <Modal open={open} onClose={onClose} title="Set a rate across multiple markets">
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          if (!gameTypeId || selected.size === 0) return;
          await bulkCreate.mutateAsync({
            market_ids: Array.from(selected),
            game_type_id: Number(gameTypeId),
            rate: Number(rate),
            effective_from: effectiveFrom,
          });
          setSelected(new Set());
          onClose();
        }}
      >
        <FormField label="Markets">
          <MarketMultiSelect markets={markets} selected={selected} onChange={setSelected} />
        </FormField>
        <FormField label="Game type">
          <Select required value={gameTypeId} onChange={(e) => setGameTypeId(Number(e.target.value))}>
            <option value="" disabled>
              Select…
            </option>
            {gameTypes?.map((gt) => (
              <option key={gt.id} value={gt.id}>
                {gt.code}
              </option>
            ))}
          </Select>
        </FormField>
        <FormField label="Rate (win per 10 credits bet)">
          <Input value={rate} onChange={(e) => setRate(e.target.value)} type="number" min={1} required placeholder="e.g. 95 or 1000" />
        </FormField>
        <FormField label="Effective from">
          <Input value={effectiveFrom} onChange={(e) => setEffectiveFrom(e.target.value)} type="date" required />
        </FormField>
        {bulkCreate.isError && <p className="mb-2 text-xs text-red-600">{(bulkCreate.error as Error).message}</p>}
        <Button type="submit" loading={bulkCreate.isPending} disabled={selected.size === 0 || !gameTypeId} className="w-full">
          Apply to {selected.size || ''} market{selected.size === 1 ? '' : 's'}
        </Button>
      </form>
    </Modal>
  );
}

export default function SimulatedRatesPage() {
  const { markets, byId } = useMarketsLookup();
  const [marketId, setMarketId] = useState<number | ''>('');
  const { data: rates, isLoading, isError, error } = useRates(marketId || null);
  const updateStatus = useUpdateRateStatus();
  const [bulkOpen, setBulkOpen] = useState(false);

  return (
    <div>
      <PageHeader
        icon="percent"
        title="Simulated Rates"
        description="Win per 10 credits bet, time-versioned via effective_from. The 'current' rate is the latest already-effective Active row."
        action={<Button onClick={() => setBulkOpen(true)}>Bulk set rate</Button>}
      />
      <BulkSetRateModal open={bulkOpen} onClose={() => setBulkOpen(false)} />
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
        Use "Bulk set rate" above to apply one rate across several markets at once, or open an individual market from the Markets section to set just its own.
      </p>
    </div>
  );
}
