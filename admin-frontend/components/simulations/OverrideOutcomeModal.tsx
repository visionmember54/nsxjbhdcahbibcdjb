'use client';

import { useState } from 'react';
import Modal from '@/components/ui/Modal';
import Button from '@/components/ui/Button';
import { FormField, Select, Textarea } from '@/components/ui/Field';
import { useOverrideSimulation } from '@/hooks/useSimulations';
import { SimulationEntry } from '@/lib/api/types';

export default function OverrideOutcomeModal({ entry, onClose }: { entry: SimulationEntry | null; onClose: () => void }) {
  const override = useOverrideSimulation();
  const [outcome, setOutcome] = useState<'Won' | 'Lost'>('Won');
  const [reason, setReason] = useState('');

  if (!entry) return null;
  const otherOutcome = entry.status === 'Won' ? 'Lost' : 'Won';

  return (
    <Modal open={!!entry} onClose={onClose} title={`Override outcome — simulation #${entry.id}`}>
      <p className="mb-3 text-xs text-slate-500">
        Overrides this one simulation&apos;s outcome for an educational demonstration. This does <strong>not</strong> change
        the underlying market result — use a result correction for that instead.
      </p>
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          if (!reason.trim()) return;
          await override.mutateAsync({ id: entry.id, outcome, reason: reason.trim() });
          onClose();
        }}
      >
        <FormField label={`Current outcome: ${entry.status}`}>
          <Select value={outcome} onChange={(e) => setOutcome(e.target.value as 'Won' | 'Lost')}>
            <option value={otherOutcome}>{otherOutcome}</option>
            <option value={entry.status}>{entry.status} (no change — will be rejected)</option>
          </Select>
        </FormField>
        <FormField label="Reason for override (required)">
          <Textarea required value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Why is this outcome being overridden?" rows={2} />
        </FormField>
        {override.isError && <p className="mb-2 text-xs text-red-600">{(override.error as Error).message}</p>}
        <Button type="submit" variant="danger" loading={override.isPending} disabled={!reason.trim()} className="w-full">
          Apply override
        </Button>
      </form>
    </Modal>
  );
}
