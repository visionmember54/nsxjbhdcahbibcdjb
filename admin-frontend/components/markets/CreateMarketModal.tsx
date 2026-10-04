'use client';

import { useState } from 'react';
import Modal from '@/components/ui/Modal';
import Button from '@/components/ui/Button';
import { FormField, Input, Select, Textarea } from '@/components/ui/Field';
import { api } from '@/lib/api/client';
import { todayLocalIso } from '@/lib/date';
import type { GameTypeConfig, Rate } from '@/lib/api/types';
import { useMarketCategories } from '@/hooks/useMarketCategories';
import { useCreateMarket } from '@/hooks/useMarkets';
import { useMarketsLookup } from '@/hooks/useMarketsLookup';
import CreateCategoryModal from './CreateCategoryModal';

/** Copies a template market's market-level (non-slot) game-type configs and
 * active rates onto a freshly created market, via the same bulk-apply
 * endpoints the Rates/Game Config pages use -- so a new market can accept
 * bets immediately instead of starting with zero games enabled. Never
 * invents a rate value; it only ever copies one that's already live
 * somewhere else in the system. */
async function copyGamesAndRatesFrom(templateMarketId: number, newMarketId: number) {
  const [configs, rates] = await Promise.all([
    api.get<GameTypeConfig[]>(`/admin/markets/${templateMarketId}/game-type-configs`),
    api.get<Rate[]>(`/admin/rates?market_id=${templateMarketId}`),
  ]);

  await Promise.all(
    configs
      .filter((c) => c.slot_id === null)
      .map((c) =>
        api.post('/admin/game-type-configs/bulk', {
          market_ids: [newMarketId],
          game_type_id: c.game_type_id,
          stage: c.stage,
          enabled: c.enabled,
          min_credits: c.min_credits,
          max_credits: c.max_credits,
          bulk_enabled: c.bulk_enabled,
          max_bulk_selections: c.max_bulk_selections,
          same_amount_allowed: c.same_amount_allowed,
          individual_amount_allowed: c.individual_amount_allowed,
          duplicate_selection_allowed: c.duplicate_selection_allowed,
          display_order: c.display_order,
        })
      )
  );

  await Promise.all(
    rates
      .filter((r) => r.slot_id === null && r.status === 'Active')
      .map((r) =>
        api.post('/admin/rates/bulk', {
          market_ids: [newMarketId],
          game_type_id: r.game_type_id,
          rate: r.rate,
          effective_from: todayLocalIso(),
        })
      )
  );
}

export default function CreateMarketModal({
  open,
  onClose,
  defaultCategorySlug,
}: {
  open: boolean;
  onClose: () => void;
  defaultCategorySlug?: string;
}) {
  const { data: categories } = useMarketCategories();
  const createMarket = useCreateMarket();
  const { markets } = useMarketsLookup();

  const [name, setName] = useState('');
  const [slug, setSlug] = useState('');
  const [isSlugTouched, setIsSlugTouched] = useState(false);
  const [categoryId, setCategoryId] = useState<number | ''>('');
  const [description, setDescription] = useState('');
  const [openingTime, setOpeningTime] = useState('');
  const [closingTime, setClosingTime] = useState('');
  const [resultTime, setResultTime] = useState('');
  const [templateMarketId, setTemplateMarketId] = useState<number | ''>('');
  const [isCategoryModalOpen, setIsCategoryModalOpen] = useState(false);
  const [copyError, setCopyError] = useState<string | null>(null);
  const [copying, setCopying] = useState(false);

  const defaultCategory = categories?.find((c) => c.slug === defaultCategorySlug);
  const effectiveCategoryId = categoryId || defaultCategory?.id || '';
  // Same-category markets first -- that's the realistic "copy this because
  // every market in this category runs the same games" case -- but any
  // market can be used as a template.
  const templateOptions = [...markets].sort((a, b) => {
    const aMatch = a.category_id === Number(effectiveCategoryId);
    const bMatch = b.category_id === Number(effectiveCategoryId);
    return aMatch === bMatch ? 0 : aMatch ? -1 : 1;
  });

  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setName(e.target.value);
    if (!isSlugTouched) {
      setSlug(e.target.value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)+/g, ''));
    }
  };

  function reset() {
    setName('');
    setSlug('');
    setIsSlugTouched(false);
    setCategoryId('');
    setDescription('');
    setOpeningTime('');
    setClosingTime('');
    setResultTime('');
    setTemplateMarketId('');
    setCopyError(null);
  }

  function handleClose() {
    reset();
    onClose();
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!effectiveCategoryId) return;
    setCopyError(null);
    const created = await createMarket.mutateAsync({
      category_id: Number(effectiveCategoryId),
      name,
      slug,
      description,
      opening_time: openingTime || null,
      closing_time: closingTime || null,
      result_time: resultTime || null,
    });
    if (templateMarketId) {
      setCopying(true);
      try {
        await copyGamesAndRatesFrom(Number(templateMarketId), created.id);
      } catch (err) {
        // The market itself was created successfully -- a failed copy just
        // means falling back to configuring it by hand, not a lost market.
        setCopyError(err instanceof Error ? err.message : 'Failed to copy game types and rates');
        setCopying(false);
        return;
      }
      setCopying(false);
    }
    reset();
    onClose();
  }

  return (
    <Modal open={open} onClose={handleClose} title="Create market">
      <form onSubmit={handleSubmit}>
        <FormField label="Name">
          <Input required value={name} onChange={handleNameChange} placeholder="e.g. MILAN DAY" />
        </FormField>
        <FormField label="Slug (unique, URL-safe)">
          <Input required value={slug} onChange={(e) => { setSlug(e.target.value); setIsSlugTouched(true); }} placeholder="e.g. milan-day" />
        </FormField>
        <FormField label="Category">
          <div className="flex gap-2">
            <Select required value={effectiveCategoryId} onChange={(e) => setCategoryId(Number(e.target.value))} className="flex-1">
              <option value="">Select category…</option>
              {categories?.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </Select>
            <Button type="button" variant="secondary" onClick={() => setIsCategoryModalOpen(true)}>
              New
            </Button>
          </div>
        </FormField>
        <FormField label="Description">
          <Textarea rows={2} value={description} onChange={(e) => setDescription(e.target.value)} />
        </FormField>
        <div className="grid grid-cols-3 gap-3">
          <FormField label="Opening time">
            <Input type="time" value={openingTime} onChange={(e) => setOpeningTime(e.target.value)} />
          </FormField>
          <FormField label="Closing time">
            <Input type="time" value={closingTime} onChange={(e) => setClosingTime(e.target.value)} />
          </FormField>
          <FormField label="Result time">
            <Input type="time" value={resultTime} onChange={(e) => setResultTime(e.target.value)} />
          </FormField>
        </div>

        <FormField label="Copy game types & rates from (optional)">
          <Select value={templateMarketId} onChange={(e) => setTemplateMarketId(e.target.value ? Number(e.target.value) : '')}>
            <option value="">Start empty -- configure games and rates later</option>
            {templateOptions.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name} ({m.category})
              </option>
            ))}
          </Select>
          <p className="mt-1 text-xs text-slate-400">
            Copies that market&rsquo;s enabled games and active rates onto this new one, so it can accept bets right away.
          </p>
        </FormField>

        {createMarket.isError && <p className="mb-3 text-xs text-red-600">{(createMarket.error as Error).message}</p>}
        {copyError && (
          <p className="mb-3 text-xs text-amber-600">
            Market was created, but copying games/rates failed: {copyError}. Configure it manually from the market page.
          </p>
        )}

        <div className="mt-4 flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={handleClose}>
            Cancel
          </Button>
          <Button type="submit" loading={createMarket.isPending || copying}>
            {templateMarketId ? 'Create & copy games/rates' : 'Create market'}
          </Button>
        </div>
      </form>
      <CreateCategoryModal
        open={isCategoryModalOpen}
        onClose={() => setIsCategoryModalOpen(false)}
        onSuccess={(id) => setCategoryId(id)}
      />
    </Modal>
  );
}
