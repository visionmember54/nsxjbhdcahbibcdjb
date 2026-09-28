'use client';

import { useEffect, useState } from 'react';
import Modal from '@/components/ui/Modal';
import Button from '@/components/ui/Button';
import { FormField, Input, Textarea, Checkbox } from '@/components/ui/Field';
import { useUpdateMarket } from '@/hooks/useMarkets';
import type { Market } from '@/lib/api/types';

const WEEKDAYS: { code: string; label: string }[] = [
  { code: 'MON', label: 'Mon' },
  { code: 'TUE', label: 'Tue' },
  { code: 'WED', label: 'Wed' },
  { code: 'THU', label: 'Thu' },
  { code: 'FRI', label: 'Fri' },
  { code: 'SAT', label: 'Sat' },
  { code: 'SUN', label: 'Sun' },
];

export default function EditMarketModal({ market, open, onClose }: { market: Market; open: boolean; onClose: () => void }) {
  const updateMarket = useUpdateMarket();

  const [name, setName] = useState(market.name);
  const [description, setDescription] = useState(market.description);
  const [openingTime, setOpeningTime] = useState(market.opening_time ?? '');
  const [closingTime, setClosingTime] = useState(market.closing_time ?? '');
  const [cutoffTime, setCutoffTime] = useState(market.cutoff_time ?? '');
  const [resultTime, setResultTime] = useState(market.result_time ?? '');
  const [visible, setVisible] = useState(market.visible);
  const [activeDays, setActiveDays] = useState<string[]>(market.active_days ?? []);

  // Re-sync whenever a different market is opened, so stale edits from a
  // previously-open market can't leak into this one.
  useEffect(() => {
    setName(market.name);
    setDescription(market.description);
    setOpeningTime(market.opening_time ?? '');
    setClosingTime(market.closing_time ?? '');
    setCutoffTime(market.cutoff_time ?? '');
    setResultTime(market.result_time ?? '');
    setVisible(market.visible);
    setActiveDays(market.active_days ?? []);
  }, [market]);

  function toggleDay(code: string) {
    setActiveDays((prev) => (prev.includes(code) ? prev.filter((d) => d !== code) : [...prev, code]));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    await updateMarket.mutateAsync({
      id: market.id,
      name,
      description,
      opening_time: openingTime || null,
      closing_time: closingTime || null,
      cutoff_time: cutoffTime || null,
      result_time: resultTime || null,
      visible,
      active_days: activeDays.length ? activeDays : null,
    });
    onClose();
  }

  return (
    <Modal open={open} onClose={onClose} title={`Edit ${market.name}`}>
      <form onSubmit={handleSubmit}>
        <FormField label="Name">
          <Input required value={name} onChange={(e) => setName(e.target.value)} />
        </FormField>
        <FormField label="Description">
          <Textarea rows={2} value={description} onChange={(e) => setDescription(e.target.value)} />
        </FormField>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <FormField label="Opening time">
            <Input type="time" value={openingTime} onChange={(e) => setOpeningTime(e.target.value)} />
          </FormField>
          <FormField label="Closing time">
            <Input type="time" value={closingTime} onChange={(e) => setClosingTime(e.target.value)} />
          </FormField>
          <FormField label="Cutoff time">
            <Input type="time" value={cutoffTime} onChange={(e) => setCutoffTime(e.target.value)} />
          </FormField>
          <FormField label="Result time">
            <Input type="time" value={resultTime} onChange={(e) => setResultTime(e.target.value)} />
          </FormField>
        </div>

        <FormField label="Active days">
          <div className="flex flex-wrap gap-3">
            {WEEKDAYS.map((d) => (
              <label key={d.code} className="flex items-center gap-1.5 text-sm text-slate-700">
                <input
                  type="checkbox"
                  checked={activeDays.includes(d.code)}
                  onChange={() => toggleDay(d.code)}
                  className="h-4 w-4 rounded border-slate-300"
                />
                {d.label}
              </label>
            ))}
          </div>
          <p className="mt-1 text-xs text-slate-400">Leave every day unchecked to run every day (the usual case).</p>
        </FormField>

        <div className="mb-4">
          <Checkbox
            label="Visible on the market page"
            checked={visible}
            onChange={(e) => setVisible(e.target.checked)}
          />
          <p className="mt-1 text-xs text-slate-400">Hidden markets stay in the admin panel but disappear from every app-facing listing.</p>
        </div>

        {updateMarket.isError && <p className="mb-3 text-xs text-red-600">{(updateMarket.error as Error).message}</p>}

        <div className="mt-4 flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" loading={updateMarket.isPending}>
            Save changes
          </Button>
        </div>
      </form>
    </Modal>
  );
}
