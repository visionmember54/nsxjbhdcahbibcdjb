'use client';

import { useState } from 'react';
import { useRates, useCreateRate, useUpdateRateStatus } from '@/hooks/useRates';
import { useGameTypes } from '@/hooks/useGameTypes';
import { Table, TBody, Td, Th, THead, Tr } from '@/components/ui/Table';
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/States';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';
import { FormField, Input, Select } from '@/components/ui/Field';
import { todayLocalIso } from '@/lib/date';

export default function RatesPanel({ marketId, slotId }: { marketId: number; slotId?: number | null }) {
  const { data: rates, isLoading, isError, error } = useRates(marketId);
  const { data: gameTypes } = useGameTypes();
  const createRate = useCreateRate();
  const updateStatus = useUpdateRateStatus();
  const [addOpen, setAddOpen] = useState(false);

  const scoped = rates?.filter((r) => (slotId ? r.slot_id === slotId : r.slot_id == null));

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-800">Simulated Rates</h3>
        <Button size="sm" variant="secondary" onClick={() => setAddOpen(true)}>
          + Set rate
        </Button>
      </div>

      {isLoading && <LoadingState />}
      {isError && <ErrorState message={(error as Error).message} />}
      {scoped && scoped.length === 0 && <EmptyState title="No rates configured yet" hint="Payouts fall back to a default rate until one is set." />}

      {scoped && scoped.length > 0 && (
        <Table>
          <THead>
            <Tr>
              <Th>Type</Th>
              <Th>Rate (per 10 credits)</Th>
              <Th>Effective from</Th>
              <Th>Status</Th>
              <Th></Th>
            </Tr>
          </THead>
          <TBody>
            {scoped.map((r) => (
              <Tr key={r.id}>
                <Td className="font-medium text-slate-900">{r.game_type_code}</Td>
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

      <Modal open={addOpen} onClose={() => setAddOpen(false)} title="Set a simulated rate">
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            const form = new FormData(e.currentTarget as HTMLFormElement);
            await createRate.mutateAsync({
              market_id: marketId,
              slot_id: slotId ?? null,
              game_type_id: Number(form.get('game_type_id')),
              rate: Number(form.get('rate')),
              effective_from: String(form.get('effective_from')),
            });
            setAddOpen(false);
          }}
        >
          <FormField label="Game type">
            <Select name="game_type_id" required defaultValue="">
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
          <FormField label="Rate (win per 10 credits staked)">
            <Input name="rate" type="number" min={1} required placeholder="e.g. 95" />
          </FormField>
          <FormField label="Effective from">
            <Input name="effective_from" type="date" required defaultValue={todayLocalIso()} />
          </FormField>
          {createRate.isError && <p className="mb-2 text-xs text-red-600">{(createRate.error as Error).message}</p>}
          <Button type="submit" loading={createRate.isPending} className="w-full">
            Save rate
          </Button>
        </form>
      </Modal>
    </div>
  );
}
