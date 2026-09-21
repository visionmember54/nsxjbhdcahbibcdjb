'use client';

import { useState } from 'react';
import { useGameTypeConfigs, useCreateGameTypeConfig, useUpdateGameTypeConfig } from '@/hooks/useGameTypeConfigs';
import { useGameTypes } from '@/hooks/useGameTypes';
import { Table, TBody, Td, Th, THead, Tr } from '@/components/ui/Table';
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/States';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';
import { Checkbox, FormField, Input, Select } from '@/components/ui/Field';
import { GameTypeConfig } from '@/lib/api/types';

export default function GameTypeConfigsPanel({ marketId, slotId }: { marketId: number; slotId?: number | null }) {
  const { data: configs, isLoading, isError, error } = useGameTypeConfigs(marketId, slotId ?? null);
  const { data: gameTypes } = useGameTypes();
  const createConfig = useCreateGameTypeConfig(marketId);
  const updateConfig = useUpdateGameTypeConfig(marketId);

  const [addOpen, setAddOpen] = useState(false);
  const [editing, setEditing] = useState<GameTypeConfig | null>(null);

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-800">Game Types</h3>
        <Button size="sm" variant="secondary" onClick={() => setAddOpen(true)}>
          + Enable game type
        </Button>
      </div>

      {isLoading && <LoadingState />}
      {isError && <ErrorState message={(error as Error).message} />}
      {configs && configs.length === 0 && <EmptyState title="No game types enabled here yet" />}

      {configs && configs.length > 0 && (
        <Table>
          <THead>
            <Tr>
              <Th>Type</Th>
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
                <Td className="font-medium text-slate-900">{c.game_type_code}</Td>
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

      <Modal open={addOpen} onClose={() => setAddOpen(false)} title="Enable a game type">
        <AddConfigForm
          gameTypes={gameTypes ?? []}
          onSubmit={async (payload) => {
            await createConfig.mutateAsync({ ...payload, slot_id: slotId ?? null });
            setAddOpen(false);
          }}
          pending={createConfig.isPending}
          error={createConfig.error as Error | null}
        />
      </Modal>

      <Modal open={!!editing} onClose={() => setEditing(null)} title={`Edit ${editing?.game_type_code ?? ''}`}>
        {editing && (
          <EditConfigForm
            config={editing}
            onSubmit={async (payload) => {
              await updateConfig.mutateAsync({ id: editing.id, ...payload });
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

function AddConfigForm({
  gameTypes,
  onSubmit,
  pending,
  error,
}: {
  gameTypes: { id: number; code: string }[];
  onSubmit: (payload: { game_type_id: number; stage: string | null }) => void;
  pending: boolean;
  error: Error | null;
}) {
  const [gameTypeId, setGameTypeId] = useState<number | ''>('');
  const [stage, setStage] = useState('');

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        if (!gameTypeId) return;
        onSubmit({ game_type_id: Number(gameTypeId), stage: stage || null });
      }}
    >
      <FormField label="Game type">
        <Select required value={gameTypeId} onChange={(e) => setGameTypeId(Number(e.target.value))}>
          <option value="">Select…</option>
          {gameTypes.map((gt) => (
            <option key={gt.id} value={gt.id}>
              {gt.code}
            </option>
          ))}
        </Select>
      </FormField>
      <FormField label="Stage (leave blank if not stage-scoped)">
        <Select value={stage} onChange={(e) => setStage(e.target.value)}>
          <option value="">—</option>
          <option value="OPEN">OPEN</option>
          <option value="CLOSE">CLOSE</option>
          <option value="BOTH">BOTH</option>
        </Select>
      </FormField>
      {error && <p className="mb-2 text-xs text-red-600">{error.message}</p>}
      <Button type="submit" loading={pending} className="w-full">
        Enable
      </Button>
    </form>
  );
}

function EditConfigForm({
  config,
  onSubmit,
  pending,
  error,
}: {
  config: GameTypeConfig;
  onSubmit: (payload: Partial<GameTypeConfig>) => void;
  pending: boolean;
  error: Error | null;
}) {
  const [enabled, setEnabled] = useState(config.enabled);
  const [minCredits, setMinCredits] = useState(config.min_credits);
  const [maxCredits, setMaxCredits] = useState(config.max_credits);
  const [bulkEnabled, setBulkEnabled] = useState(config.bulk_enabled);
  const [maxBulk, setMaxBulk] = useState(config.max_bulk_selections);
  const [sameAmount, setSameAmount] = useState(config.same_amount_allowed);
  const [individualAmount, setIndividualAmount] = useState(config.individual_amount_allowed);
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
          same_amount_allowed: sameAmount,
          individual_amount_allowed: individualAmount,
          duplicate_selection_allowed: duplicates,
        });
      }}
    >
      <FormField label="">
        <Checkbox label="Enabled" checked={enabled} onChange={(e) => setEnabled(e.target.checked)} />
      </FormField>
      <div className="grid grid-cols-2 gap-3">
        <FormField label="Min credits">
          <Input type="number" min={1} value={minCredits} onChange={(e) => setMinCredits(Number(e.target.value))} />
        </FormField>
        <FormField label="Max credits">
          <Input type="number" min={1} value={maxCredits} onChange={(e) => setMaxCredits(Number(e.target.value))} />
        </FormField>
      </div>
      <FormField label="">
        <Checkbox label="Bulk selection enabled" checked={bulkEnabled} onChange={(e) => setBulkEnabled(e.target.checked)} />
      </FormField>
      <FormField label="Max bulk selections">
        <Input type="number" min={1} value={maxBulk} onChange={(e) => setMaxBulk(Number(e.target.value))} />
      </FormField>
      <div className="space-y-2">
        <Checkbox label="Same amount for all selections allowed" checked={sameAmount} onChange={(e) => setSameAmount(e.target.checked)} />
        <Checkbox
          label="Individual amount per selection allowed"
          checked={individualAmount}
          onChange={(e) => setIndividualAmount(e.target.checked)}
        />
        <Checkbox label="Duplicate selections allowed in one batch" checked={duplicates} onChange={(e) => setDuplicates(e.target.checked)} />
      </div>

      {error && <p className="mb-2 mt-3 text-xs text-red-600">{error.message}</p>}
      <Button type="submit" loading={pending} className="mt-4 w-full">
        Save changes
      </Button>
    </form>
  );
}
