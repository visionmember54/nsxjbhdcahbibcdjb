'use client';

import { useState } from 'react';
import Modal from '@/components/ui/Modal';
import Button from '@/components/ui/Button';
import { Checkbox, FormField, Input, Select } from '@/components/ui/Field';
import MarketMultiSelect from '@/components/markets/MarketMultiSelect';
import { useMarketsLookup } from '@/hooks/useMarketsLookup';
import { useApplyGameTypeConfigBulk } from '@/hooks/useGameTypeConfigs';

/** Lets an admin enable (or re-tune) one game type across many markets in a
 * single submission -- for a category like Gali-Disawar where every market
 * is meant to offer the exact same games, this replaces opening each market
 * individually just to flip the same switch everywhere. Market-level only;
 * Starline slots still go through the per-market panel since slots can
 * legitimately differ from each other. */
export default function BulkApplyGameTypeConfigModal({
  open,
  onClose,
  gameTypeId,
  gameTypeLabel,
}: {
  open: boolean;
  onClose: () => void;
  gameTypeId: number;
  gameTypeLabel: string;
}) {
  const { markets } = useMarketsLookup();
  const apply = useApplyGameTypeConfigBulk();
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [stage, setStage] = useState('');
  const [enabled, setEnabled] = useState(true);
  const [minCredits, setMinCredits] = useState(10);
  const [maxCredits, setMaxCredits] = useState(10000);
  const [bulkEnabled, setBulkEnabled] = useState(true);
  const [maxBulk, setMaxBulk] = useState(50);

  return (
    <Modal open={open} onClose={onClose} title={`Apply ${gameTypeLabel} to markets`}>
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          if (selected.size === 0) return;
          await apply.mutateAsync({
            market_ids: Array.from(selected),
            game_type_id: gameTypeId,
            stage: stage || null,
            enabled,
            min_credits: minCredits,
            max_credits: maxCredits,
            bulk_enabled: bulkEnabled,
            max_bulk_selections: maxBulk,
          });
          setSelected(new Set());
          onClose();
        }}
      >
        <FormField label="Markets">
          <MarketMultiSelect markets={markets} selected={selected} onChange={setSelected} />
        </FormField>
        <FormField label="Stage (leave blank if not stage-scoped)">
          <Select value={stage} onChange={(e) => setStage(e.target.value)}>
            <option value="">—</option>
            <option value="OPEN">OPEN</option>
            <option value="CLOSE">CLOSE</option>
            <option value="BOTH">BOTH</option>
          </Select>
        </FormField>
        <Checkbox label="Enabled" checked={enabled} onChange={(e) => setEnabled(e.target.checked)} />
        <div className="my-3 grid grid-cols-2 gap-3">
          <FormField label="Min credits">
            <Input type="number" min={1} value={minCredits} onChange={(e) => setMinCredits(Number(e.target.value))} />
          </FormField>
          <FormField label="Max credits">
            <Input type="number" min={1} value={maxCredits} onChange={(e) => setMaxCredits(Number(e.target.value))} />
          </FormField>
        </div>
        <Checkbox label="Bulk selection enabled" checked={bulkEnabled} onChange={(e) => setBulkEnabled(e.target.checked)} />
        <FormField label="Max bulk selections">
          <Input type="number" min={1} value={maxBulk} onChange={(e) => setMaxBulk(Number(e.target.value))} />
        </FormField>

        {apply.isError && <p className="mb-2 mt-3 text-xs text-red-600">{(apply.error as Error).message}</p>}
        <Button type="submit" loading={apply.isPending} disabled={selected.size === 0} className="mt-4 w-full">
          Apply to {selected.size || ''} market{selected.size === 1 ? '' : 's'}
        </Button>
      </form>
    </Modal>
  );
}
