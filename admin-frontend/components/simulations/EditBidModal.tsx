'use client';

import { useEffect, useState } from 'react';
import Modal from '@/components/ui/Modal';
import Button from '@/components/ui/Button';
import { FormField, Input } from '@/components/ui/Field';
import { useEditSimulation } from '@/hooks/useSimulations';
import { SimulationEntry } from '@/lib/api/types';

export default function EditBidModal({ entry, onClose }: { entry: SimulationEntry | null; onClose: () => void }) {
  const edit = useEditSimulation();
  const [selection, setSelection] = useState('');
  const [credits, setCredits] = useState('');

  useEffect(() => {
    if (entry) {
      setSelection(entry.selection);
      setCredits(String(entry.simulatedCredits));
    }
  }, [entry]);

  if (!entry) return null;

  return (
    <Modal open={!!entry} onClose={onClose} title={`Edit bid — #${entry.id}`}>
      <p className="mb-3 text-xs text-slate-500">
        Corrects a mistaken entry before it resolves — the number picked and/or the points staked. Only Pending bids
        can be edited; once a result is published this option disappears.
      </p>
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          if (!selection.trim() || !credits) return;
          await edit.mutateAsync({ id: entry.id, selection: selection.trim(), credits: Number(credits) });
          onClose();
        }}
      >
        <FormField label="Selection">
          <Input required value={selection} onChange={(e) => setSelection(e.target.value)} placeholder="e.g. 5, 45, or 128" />
        </FormField>
        <FormField label="Points (credits)">
          <Input required type="number" min={1} value={credits} onChange={(e) => setCredits(e.target.value)} />
        </FormField>
        {edit.isError && <p className="mb-2 text-xs text-red-600">{(edit.error as Error).message}</p>}
        <Button type="submit" loading={edit.isPending} disabled={!selection.trim() || !credits} className="w-full">
          Save correction
        </Button>
      </form>
    </Modal>
  );
}
