'use client';

import { useState } from 'react';
import { GameTypeConfigWithMarket, useUpdateGameTypeConfigCrossMarket } from '@/hooks/useGameTypeConfigs';
import { Table, TBody, Td, Th, THead, Tr } from '@/components/ui/Table';
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/States';
import Badge from '@/components/ui/Badge';
import Modal from '@/components/ui/Modal';
import { Checkbox, FormField, Input } from '@/components/ui/Field';
import Button from '@/components/ui/Button';

export default function GameConfigTable({
  configs,
  isLoading,
  isError,
  errorMessage,
}: {
  configs: GameTypeConfigWithMarket[] | undefined;
  isLoading: boolean;
  isError: boolean;
  errorMessage?: string;
}) {
  const updateConfig = useUpdateGameTypeConfigCrossMarket();
  const [editing, setEditing] = useState<GameTypeConfigWithMarket | null>(null);

  return (
    <div>
      {isLoading && <LoadingState />}
      {isError && <ErrorState message={errorMessage ?? 'Failed to load'} />}
      {configs && configs.length === 0 && <EmptyState title="Not enabled on any market yet" hint="Enable it from a market's detail page." />}

      {configs && configs.length > 0 && (
        <Table>
          <THead>
            <Tr>
              <Th>Market</Th>
              <Th>Category</Th>
              <Th>Stage</Th>
              <Th>Enabled</Th>
              <Th>Credits</Th>
              <Th>Bulk</Th>
              <Th></Th>
            </Tr>
          </THead>
          <TBody>
            {configs.map((c) => (
              <Tr key={c.id}>
                <Td className="font-medium text-slate-900">{c.marketName}</Td>
                <Td>{c.marketCategory}</Td>
                <Td>{c.stage ?? '—'}</Td>
                <Td>
                  <Badge tone={c.enabled ? 'green' : 'slate'}>{c.enabled ? 'Enabled' : 'Disabled'}</Badge>
                </Td>
                <Td>
                  {c.min_credits}–{c.max_credits}
                </Td>
                <Td>{c.bulk_enabled ? `up to ${c.max_bulk_selections}` : 'off'}</Td>
                <Td>
                  <button className="text-xs font-semibold text-brand-600 hover:underline" onClick={() => setEditing(c)}>
                    Edit
                  </button>
                </Td>
              </Tr>
            ))}
          </TBody>
        </Table>
      )}

      <Modal open={!!editing} onClose={() => setEditing(null)} title={editing ? `${editing.game_type_code} on ${editing.marketName}` : ''}>
        {editing && (
          <RowEditForm
            config={editing}
            onSubmit={async (payload) => {
              await updateConfig.mutateAsync({ marketId: editing.market_id, id: editing.id, ...payload });
              setEditing(null);
            }}
            pending={updateConfig.isPending}
            error={updateConfig.error as Error | null}
          />
        )}
      </Modal>
    </div>
  );
}

function RowEditForm({
  config,
  onSubmit,
  pending,
  error,
}: {
  config: GameTypeConfigWithMarket;
  onSubmit: (payload: Record<string, unknown>) => void;
  pending: boolean;
  error: Error | null;
}) {
  const [enabled, setEnabled] = useState(config.enabled);
  const [minCredits, setMinCredits] = useState(config.min_credits);
  const [maxCredits, setMaxCredits] = useState(config.max_credits);
  const [bulkEnabled, setBulkEnabled] = useState(config.bulk_enabled);
  const [maxBulk, setMaxBulk] = useState(config.max_bulk_selections);
  const [duplicates, setDuplicates] = useState(config.duplicate_selection_allowed);

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit({
          enabled,
          min_credits: minCredits,
          max_credits: maxCredits,
          bulk_enabled: bulkEnabled,
          max_bulk_selections: maxBulk,
          duplicate_selection_allowed: duplicates,
        });
      }}
    >
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
      <Checkbox label="Duplicate selections allowed in one batch" checked={duplicates} onChange={(e) => setDuplicates(e.target.checked)} />

      {error && <p className="mb-2 mt-3 text-xs text-red-600">{error.message}</p>}
      <Button type="submit" loading={pending} className="mt-4 w-full">
        Save changes
      </Button>
    </form>
  );
}
