'use client';

import { useState } from 'react';
import Modal from '@/components/ui/Modal';
import Button from '@/components/ui/Button';
import { FormField, Input, Textarea } from '@/components/ui/Field';
import { useCorrectResult } from '@/hooks/useResults';
import { MarketResult } from '@/lib/api/types';

export default function CorrectResultModal({ result, onClose }: { result: MarketResult | null; onClose: () => void }) {
  const correctResult = useCorrectResult();
  const [openPanna, setOpenPanna] = useState('');
  const [closePanna, setClosePanna] = useState('');
  const [singleResult, setSingleResult] = useState('');
  const [reason, setReason] = useState('');

  if (!result) return null;

  return (
    <Modal open={!!result} onClose={onClose} title={`Correct result #${result.id}`}>
      <p className="mb-3 text-xs text-slate-500">
        Corrections reverse any payouts already made and re-evaluate every pending selection against the new result. This
        creates a new record linked to the original for the audit trail.
      </p>
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          if (!reason.trim()) return;
          await correctResult.mutateAsync({
            id: result.id,
            reason: reason.trim(),
            open_panna: openPanna || undefined,
            close_panna: closePanna || undefined,
            single_result: singleResult || undefined,
          });
          onClose();
        }}
      >
        <FormField label={`Open Panna (current: ${result.openPanna ?? '—'})`}>
          <Input value={openPanna} onChange={(e) => setOpenPanna(e.target.value)} placeholder="3 digits" maxLength={3} />
        </FormField>
        <FormField label={`Close Panna (current: ${result.closePanna ?? '—'})`}>
          <Input value={closePanna} onChange={(e) => setClosePanna(e.target.value)} placeholder="3 digits" maxLength={3} />
        </FormField>
        <FormField label={`Single result (current: ${result.singleResult ?? '—'})`}>
          <Input value={singleResult} onChange={(e) => setSingleResult(e.target.value)} placeholder="for Starline/Gali-Disawar" />
        </FormField>
        <FormField label="Reason for correction (required)">
          <Textarea required value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Why is this result being corrected?" rows={2} />
        </FormField>
        {correctResult.isError && <p className="mb-2 text-xs text-red-600">{(correctResult.error as Error).message}</p>}
        <Button type="submit" variant="danger" loading={correctResult.isPending} disabled={!reason.trim()} className="w-full">
          Apply correction
        </Button>
      </form>
    </Modal>
  );
}
