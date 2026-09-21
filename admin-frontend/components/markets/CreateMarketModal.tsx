'use client';

import { useState } from 'react';
import Modal from '@/components/ui/Modal';
import Button from '@/components/ui/Button';
import { FormField, Input, Select, Textarea } from '@/components/ui/Field';
import { useMarketCategories } from '@/hooks/useMarketCategories';
import { useCreateMarket } from '@/hooks/useMarkets';
import CreateCategoryModal from './CreateCategoryModal';

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
  const [isSlugTouched, setIsSlugTouched] = useState(false);
  const [categoryId, setCategoryId] = useState<number | ''>('');
  const [description, setDescription] = useState('');
  const [openingTime, setOpeningTime] = useState('');
  const [closingTime, setClosingTime] = useState('');
  const [resultTime, setResultTime] = useState('');
  const [isCategoryModalOpen, setIsCategoryModalOpen] = useState(false);

  const defaultCategory = categories?.find((c) => c.slug === defaultCategorySlug);
  const effectiveCategoryId = categoryId || defaultCategory?.id || '';

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
  }

  function handleClose() {
    reset();
    onClose();
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

        {createMarket.isError && <p className="mb-3 text-xs text-red-600">{(createMarket.error as Error).message}</p>}

        <div className="mt-4 flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={handleClose}>
            Cancel
          </Button>
          <Button type="submit" loading={createMarket.isPending}>
            Create market
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
