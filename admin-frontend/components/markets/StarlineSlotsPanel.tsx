'use client';

import { Fragment, useState } from 'react';
import { useStarlineSlots, useCreateStarlineSlot, useUpdateStarlineSlot } from '@/hooks/useStarline';
import { Table, TBody, Td, Th, THead, Tr } from '@/components/ui/Table';
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/States';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';
import { FormField, Input } from '@/components/ui/Field';
import GameTypeConfigsPanel from './GameTypeConfigsPanel';
import RatesPanel from './RatesPanel';

export default function StarlineSlotsPanel({ marketId }: { marketId: number }) {
  const { data: slots, isLoading, isError, error } = useStarlineSlots(marketId);
  const createSlot = useCreateStarlineSlot();
  const updateSlot = useUpdateStarlineSlot();
  const [addOpen, setAddOpen] = useState(false);
  const [expanded, setExpanded] = useState<number | null>(null);

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-800">Daily Slots</h3>
        <Button size="sm" variant="secondary" onClick={() => setAddOpen(true)}>
          + Add slot
        </Button>
      </div>

      {isLoading && <LoadingState />}
      {isError && <ErrorState message={(error as Error).message} />}
      {slots && slots.length === 0 && <EmptyState title="No slots yet" hint="Add daily time windows like 10:00 AM, 11:00 AM, ..." />}

      {slots && slots.length > 0 && (
        <Table>
          <THead>
            <Tr>
              <Th>Slot</Th>
              <Th>Start</Th>
              <Th>Cutoff</Th>
              <Th>Status</Th>
              <Th></Th>
            </Tr>
          </THead>
          <TBody>
            {slots.map((slot) => (
              <Fragment key={slot.id}>
                <Tr>
                  <Td className="font-medium text-slate-900">{slot.slot_name}</Td>
                  <Td>{slot.start_time}</Td>
                  <Td>{slot.cutoff_time}</Td>
                  <Td>
                    <Badge tone={slot.enabled ? 'green' : 'slate'}>{slot.enabled ? 'Enabled' : 'Disabled'}</Badge>
                  </Td>
                  <Td className="space-x-3">
                    <button
                      className="text-xs font-semibold text-brand-600 hover:underline"
                      onClick={() => setExpanded(expanded === slot.id ? null : slot.id)}
                    >
                      {expanded === slot.id ? 'Hide' : 'Configure'}
                    </button>
                    <button
                      className="text-xs font-semibold text-slate-500 hover:underline"
                      onClick={() => updateSlot.mutate({ id: slot.id, enabled: !slot.enabled })}
                    >
                      {slot.enabled ? 'Disable' : 'Enable'}
                    </button>
                  </Td>
                </Tr>
                {expanded === slot.id && (
                  <Tr>
                    <Td colSpan={5} className="bg-slate-50">
                      <div className="space-y-6 py-2">
                        <GameTypeConfigsPanel marketId={marketId} slotId={slot.id} />
                        <RatesPanel marketId={marketId} slotId={slot.id} />
                      </div>
                    </Td>
                  </Tr>
                )}
              </Fragment>
            ))}
          </TBody>
        </Table>
      )}

      <Modal open={addOpen} onClose={() => setAddOpen(false)} title="Add a Starline slot">
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            const form = new FormData(e.currentTarget as HTMLFormElement);
            await createSlot.mutateAsync({
              market_id: marketId,
              slot_name: String(form.get('slot_name')),
              start_time: String(form.get('start_time')),
              cutoff_time: String(form.get('cutoff_time')),
            });
            setAddOpen(false);
          }}
        >
          <FormField label="Slot name">
            <Input name="slot_name" required placeholder="e.g. 10:00 AM" />
          </FormField>
          <FormField label="Start time">
            <Input name="start_time" type="time" required />
          </FormField>
          <FormField label="Cutoff time">
            <Input name="cutoff_time" type="time" required />
          </FormField>
          {createSlot.isError && <p className="mb-2 text-xs text-red-600">{(createSlot.error as Error).message}</p>}
          <Button type="submit" loading={createSlot.isPending} className="w-full">
            Add slot
          </Button>
        </form>
      </Modal>
    </div>
  );
}
