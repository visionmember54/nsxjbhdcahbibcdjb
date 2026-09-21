'use client';

import { useState } from 'react';
import Modal from '@/components/ui/Modal';
import Button from '@/components/ui/Button';
import { FormField, Input, Select, Textarea } from '@/components/ui/Field';
import { useMarketCategories } from '@/hooks/useMarketCategories';
import { useCreateMarket } from '@/hooks/useMarkets';

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

  const [name, setName] = useState('');
  const [slug, setSlug] = useState('');
  const [categoryId, setCategoryId] = useState<number | ''>('');
  const [description, setDescription] = useState('');
  const [openingTime, setOpeningTime] = useState('');
  const [closingTime, setClosingTime] = useState('');
  const [resultTime, setResultTime] = useState('');

  const defaultCategory = categories?.find((c) => c.slug === defaultCategorySlug);
  const effectiveCategoryId = categoryId || defaultCategory?.id || '';

  function reset() {
    setName('');
    setSlug('');
    setCategoryId('');
    setDescription('');
    setOpeningTime('');
    setClosingTime('');
    setResultTime('');
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!effectiveCategoryId) return;
    await createMarket.mutateAsync({
      category_id: Number(effectiveCategoryId),
      name,
      slug,
      description,
      opening_time: openingTime || null,
      closing_time: closingTime || null,
      result_time: resultTime || null,
    });
    reset();
    onClose();
  }

  return (
    <Modal open={open} onClose={onClose} title="Create market">
      <form onSubmit={handleSubmit}>
        <FormField label="Name">
          <Input required value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. MILAN DAY" />
        </FormField>
        <FormField label="Slug (unique, URL-safe)">
          <Input required value={slug} onChange={(e) => setSlug(e.target.value)} placeholder="e.g. milan-day" />
        </FormField>
        <FormField label="Category">
          <Select required value={effectiveCategoryId} onChange={(e) => setCategoryId(Number(e.target.value))}>
            <option value="">Select category…</option>
            {categories?.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </Select>
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

        {createMarket.isError && <p className="mb-3 text-xs text-red-600">{(createMarket.error as Error).message}</p>}

        <div className="mt-4 flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" loading={createMarket.isPending}>
            Create market
          </Button>
        </div>
      </form>
    </Modal>
  );
}
