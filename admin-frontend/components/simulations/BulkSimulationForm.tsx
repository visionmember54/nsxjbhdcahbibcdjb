'use client';

import { useState } from 'react';
import { useMarketsLookup } from '@/hooks/useMarketsLookup';
import { useStarlineSlots } from '@/hooks/useStarline';
import { useGameTypes } from '@/hooks/useGameTypes';
import { useStudents } from '@/hooks/useStudents';
import { useCreateBulkSimulation } from '@/hooks/useSimulations';
import { FormField, Input, Select } from '@/components/ui/Field';
import Button from '@/components/ui/Button';

interface Row {
  value: string;
  credits: string;
  game_variant: '' | 'OPEN_PANNA_CLOSE_ANK' | 'OPEN_ANK_CLOSE_PANNA';
}

export default function BulkSimulationForm({ onDone }: { onDone?: () => void }) {
  const { markets } = useMarketsLookup();
  const { data: gameTypes } = useGameTypes();
  const { data: studentsPage } = useStudents({ limit: 100 });
  const createBulk = useCreateBulkSimulation();

  const [studentId, setStudentId] = useState<number | ''>('');
  const [marketId, setMarketId] = useState<number | ''>('');
  const [slotId, setSlotId] = useState<number | ''>('');
  const [gameType, setGameType] = useState('');
  const [stage, setStage] = useState('');
  const [rows, setRows] = useState<Row[]>([{ value: '', credits: '', game_variant: '' }]);

  const selectedMarket = markets.find((m) => m.id === marketId);
  const isStarline = selectedMarket?.category === 'STARLINE';
  const { data: slots } = useStarlineSlots(isStarline ? Number(marketId) : null);

  const totalCredits = rows.reduce((sum, r) => sum + (Number(r.credits) || 0), 0);

  function updateRow(index: number, field: keyof Row, value: string) {
    setRows((prev) => prev.map((r, i) => (i === index ? { ...r, [field]: value } : r)));
  }

  return (
    <form
      onSubmit={async (e) => {
        e.preventDefault();
        if (!studentId || !marketId || !gameType) return;
        await createBulk.mutateAsync({
          user_id: Number(studentId),
          market_id: Number(marketId),
          slot_id: isStarline ? Number(slotId) || null : null,
          game_type: gameType,
          stage: stage || null,
          selections: rows.filter((r) => r.value && r.credits).map((r) => ({ value: r.value.trim(), credits: Number(r.credits), game_variant: r.game_variant || undefined })),
        });
        setRows([{ value: '', credits: '', game_variant: '' }]);
        onDone?.();
      }}
    >
      <div className="grid grid-cols-2 gap-3">
        <FormField label="User">
          <Select required value={studentId} onChange={(e) => setStudentId(Number(e.target.value))}>
            <option value="">Select…</option>
            {studentsPage?.items.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name} ({s.balance} credits)
              </option>
            ))}
          </Select>
        </FormField>
        <FormField label="Market">
          <Select required value={marketId} onChange={(e) => setMarketId(Number(e.target.value))}>
            <option value="">Select…</option>
            {markets.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name}
              </option>
            ))}
          </Select>
        </FormField>
        {isStarline && (
          <FormField label="Slot">
            <Select required value={slotId} onChange={(e) => setSlotId(Number(e.target.value))}>
              <option value="">Select…</option>
              {slots?.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.slot_name}
                </option>
              ))}
            </Select>
          </FormField>
        )}
        <FormField label="Game type">
          <Select required value={gameType} onChange={(e) => setGameType(e.target.value)}>
            <option value="">Select…</option>
            {gameTypes?.map((gt) => (
              <option key={gt.id} value={gt.code}>
                {gt.code}
              </option>
            ))}
          </Select>
        </FormField>
        <FormField label="Stage (if applicable)">
          <Select value={stage} onChange={(e) => setStage(e.target.value)}>
            <option value="">—</option>
            <option value="OPEN">OPEN</option>
            <option value="CLOSE">CLOSE</option>
          </Select>
        </FormField>
      </div>

      <div className="mt-3">
        <div className="mb-2 flex items-center justify-between">
          <p className="text-xs font-semibold text-slate-600">Selections</p>
          <button
            type="button"
            className="text-xs font-semibold text-brand-600 hover:underline"
            onClick={() => setRows((prev) => [...prev, { value: '', credits: '', game_variant: '' }])}
          >
            + Add row
          </button>
        </div>
        <div className="space-y-2">
          {rows.map((row, i) => (
            <div key={i} className="flex items-center gap-2">
              <Input placeholder={gameType === 'HALF_SANGAM' ? 'Panna-Ank (e.g. 128-4)' : gameType === 'FULL_SANGAM' ? 'Panna-Panna (e.g. 128-470)' : 'Value (e.g. 16)'} value={row.value} onChange={(e) => updateRow(i, 'value', e.target.value)} />
              {gameType === 'HALF_SANGAM' && <Select value={row.game_variant} onChange={(e) => updateRow(i, 'game_variant', e.target.value)}><option value="">Direction…</option><option value="OPEN_PANNA_CLOSE_ANK">Open Panna → Close Ank</option><option value="OPEN_ANK_CLOSE_PANNA">Close Panna → Open Ank</option></Select>}
              <Input
                type="number"
                min={1}
                placeholder="Credits"
                value={row.credits}
                onChange={(e) => updateRow(i, 'credits', e.target.value)}
              />
              {rows.length > 1 && (
                <button
                  type="button"
                  className="shrink-0 text-xs font-semibold text-red-500 hover:underline"
                  onClick={() => setRows((prev) => prev.filter((_, idx) => idx !== i))}
                >
                  Remove
                </button>
              )}
            </div>
          ))}
        </div>
        <p className="mt-2 text-xs text-slate-500">
          {rows.length} selection{rows.length !== 1 ? 's' : ''} · {totalCredits} credits total
        </p>
      </div>

      {createBulk.isError && <p className="mb-2 mt-3 text-xs text-red-600">{(createBulk.error as Error).message}</p>}
      {createBulk.isSuccess && (
        <p className="mb-2 mt-3 text-xs text-emerald-600">
          Submitted — batch #{createBulk.data.batchId}, remaining balance {createBulk.data.remainingBalance}.
        </p>
      )}

      <Button type="submit" loading={createBulk.isPending} className="mt-3 w-full">
        Submit batch
      </Button>
    </form>
  );
}
