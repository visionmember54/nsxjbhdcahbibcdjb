'use client';

import { useEffect, useState } from 'react';
import { useMarketsLookup } from '@/hooks/useMarketsLookup';
import { useStarlineSlots } from '@/hooks/useStarline';
import { useUpsertResult, usePreviewResult } from '@/hooks/useResults';
import { Checkbox, FormField, Input, Select } from '@/components/ui/Field';
import Button from '@/components/ui/Button';
import Badge from '@/components/ui/Badge';
import { Table, TBody, Td, Th, THead, Tr } from '@/components/ui/Table';
import { Icon } from '@/components/layout/icons';
import { todayLocalIso } from '@/lib/date';

function PreviewStat({
  icon,
  tone,
  label,
  value,
}: {
  icon: 'users' | 'coin' | 'clock' | 'check';
  tone: 'emerald' | 'brand' | 'amber' | 'slate';
  label: string;
  value: string | number;
}) {
  const toneClasses: Record<string, string> = {
    emerald: 'bg-emerald-50 text-emerald-600',
    brand: 'bg-brand-50 text-brand-600',
    amber: 'bg-amber-50 text-amber-600',
    slate: 'bg-slate-100 text-slate-500',
  };
  return (
    <div className="flex items-center gap-2.5 rounded-lg border border-slate-200/80 bg-white px-3 py-2.5 shadow-soft">
      <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${toneClasses[tone]}`}>
        <Icon name={icon} className="h-4 w-4" />
      </span>
      <div>
        <p className="text-[11px] font-medium uppercase tracking-wide text-slate-500">{label}</p>
        <p className="text-sm font-bold text-slate-900">{value}</p>
      </div>
    </div>
  );
}

export default function PublishResultForm() {
  const { markets } = useMarketsLookup();
  const upsertResult = useUpsertResult();
  const previewResult = usePreviewResult();

  const [marketId, setMarketId] = useState<number | ''>('');
  const [slotId, setSlotId] = useState<number | ''>('');
  const [date, setDate] = useState(todayLocalIso());
  const [openPanna, setOpenPanna] = useState('');
  const [openAnk, setOpenAnk] = useState('');
  const [closePanna, setClosePanna] = useState('');
  const [closeAnk, setCloseAnk] = useState('');
  const [singleResult, setSingleResult] = useState('');
  const [publish, setPublish] = useState(true);

  const selectedMarket = markets.find((m) => m.id === marketId);
  const isStarline = selectedMarket?.category === 'STARLINE';
  const { data: slots } = useStarlineSlots(isStarline ? Number(marketId) : null);

  // A stale preview for a different market/slot is worse than no preview.
  useEffect(() => {
    previewResult.reset();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [marketId, slotId]);

  function reset() {
    setOpenPanna('');
    setOpenAnk('');
    setClosePanna('');
    setCloseAnk('');
    setSingleResult('');
    previewResult.reset();
  }

  const canPreview = !!marketId && (!!openPanna || !!openAnk || !!closePanna || !!closeAnk);
  const preview = previewResult.data;

  return (
    <form
      onSubmit={async (e) => {
        e.preventDefault();
        if (!marketId) return;
        await upsertResult.mutateAsync({
          market_id: Number(marketId),
          slot_id: isStarline ? Number(slotId) || null : null,
          date,
          open_panna: openPanna || null,
          open_ank: !openPanna && openAnk ? openAnk : null,
          close_panna: closePanna || null,
          close_ank: !closePanna && closeAnk ? closeAnk : null,
          single_result: singleResult || null,
          publish,
        });
        reset();
      }}
    >
      <div className="grid grid-cols-2 gap-3">
        <FormField label="Market">
          <Select required value={marketId} onChange={(e) => setMarketId(Number(e.target.value))}>
            <option value="">Select…</option>
            {markets.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name} ({m.category})
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
        <FormField label="Date">
          <Input type="date" required value={date} onChange={(e) => setDate(e.target.value)} />
        </FormField>
      </div>

      <div className="mt-2 grid grid-cols-2 gap-3 rounded-lg bg-slate-50 p-3">
        <FormField label="Open Panna (3 digits — derives Open Ank)">
          <Input value={openPanna} onChange={(e) => setOpenPanna(e.target.value)} maxLength={3} placeholder="e.g. 128" />
        </FormField>
        <FormField label="Open Ank (if no panna, e.g. Gali-Disawar)">
          <Input value={openAnk} onChange={(e) => setOpenAnk(e.target.value)} maxLength={1} placeholder="0-9" disabled={!!openPanna} />
        </FormField>
        <FormField label="Close Panna (3 digits — derives Close Ank)">
          <Input value={closePanna} onChange={(e) => setClosePanna(e.target.value)} maxLength={3} placeholder="e.g. 600" />
        </FormField>
        <FormField label="Close Ank (if no panna)">
          <Input value={closeAnk} onChange={(e) => setCloseAnk(e.target.value)} maxLength={1} placeholder="0-9" disabled={!!closePanna} />
        </FormField>
      </div>

      <FormField label="Single result (free text fallback)">
        <Input value={singleResult} onChange={(e) => setSingleResult(e.target.value)} placeholder="Only if not open/close/panna shaped" />
      </FormField>

      <Button
        type="button"
        variant="secondary"
        className="w-full"
        disabled={!canPreview}
        loading={previewResult.isPending}
        onClick={() =>
          previewResult.mutate({
            market_id: Number(marketId),
            slot_id: isStarline ? Number(slotId) || null : null,
            open_panna: openPanna || null,
            open_ank: !openPanna && openAnk ? openAnk : null,
            close_panna: closePanna || null,
            close_ank: !closePanna && closeAnk ? closeAnk : null,
          })
        }
      >
        <Icon name="chart" className="h-4 w-4" />
        Preview winners
      </Button>

      {previewResult.isError && (
        <p className="mt-2 text-xs text-red-600">{(previewResult.error as Error).message}</p>
      )}

      {preview && (
        <div className="mt-3 rounded-xl border border-slate-200/80 bg-slate-50/60 p-3">
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            <PreviewStat icon="check" tone="emerald" label="Winners" value={preview.winnersCount} />
            <PreviewStat icon="coin" tone="brand" label="Potential payout" value={preview.totalPotentialPayout.toLocaleString()} />
            <PreviewStat icon="users" tone="slate" label="Stake at risk" value={preview.totalStakeAtRisk.toLocaleString()} />
            <PreviewStat icon="clock" tone="amber" label="Unresolved" value={preview.unresolvedEntries} />
          </div>

          {preview.jodi && (
            <p className="mt-2.5 text-xs text-slate-500">
              Derived jodi: <span className="font-semibold text-slate-800">{preview.jodi}</span>
            </p>
          )}

          {preview.winnersCount > 0 ? (
            <div className="mt-3 overflow-hidden rounded-lg border border-slate-200 bg-white">
              <Table>
                <THead>
                  <Tr>
                    <Th>User</Th>
                    <Th>Game</Th>
                    <Th>Selection</Th>
                    <Th>Credits</Th>
                    <Th>Payout</Th>
                  </Tr>
                </THead>
                <TBody>
                  {preview.winners.map((w) => (
                    <Tr key={w.entryId}>
                      <Td className="font-medium text-slate-900">
                        {w.userName}
                        <span className="ml-1.5 text-xs font-normal text-slate-400">{w.userPhone}</span>
                      </Td>
                      <Td>
                        <Badge tone="green">{w.gameType.replace('_', ' ')}</Badge>
                      </Td>
                      <Td className="font-mono text-xs">{w.selection}</Td>
                      <Td>{w.credits.toLocaleString()}</Td>
                      <Td className="font-semibold text-emerald-600">{w.potentialPayout.toLocaleString()}</Td>
                    </Tr>
                  ))}
                </TBody>
              </Table>
            </div>
          ) : (
            <p className="mt-3 text-xs text-slate-500">
              {preview.resolvableEntries === 0
                ? 'No pending simulations for this market/slot yet.'
                : `No one wins with this result — ${preview.resolvableEntries} pending ${preview.resolvableEntries === 1 ? 'entry' : 'entries'} would lose.`}
            </p>
          )}
        </div>
      )}

      <Checkbox label="Publish now (unchecked saves as draft)" checked={publish} onChange={(e) => setPublish(e.target.checked)} />

      {upsertResult.isError && <p className="mb-2 mt-3 text-xs text-red-600">{(upsertResult.error as Error).message}</p>}
      {upsertResult.isSuccess && <p className="mb-2 mt-3 text-xs text-emerald-600">Saved.</p>}

      <Button type="submit" loading={upsertResult.isPending} className="mt-4 w-full">
        {publish ? 'Publish result' : 'Save draft'}
      </Button>
    </form>
  );
}
