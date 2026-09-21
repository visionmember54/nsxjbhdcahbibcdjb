'use client';

import { useState } from 'react';
import Modal from '@/components/ui/Modal';
import Button from '@/components/ui/Button';
import { FormField, Input } from '@/components/ui/Field';
import { useCreateMarketCategory } from '@/hooks/useMarketCategories';

export default function CreateCategoryModal({
  open,
  onClose,
  onSuccess,
}: {
  open: boolean;
  onClose: () => void;
  onSuccess?: (categoryId: number) => void;
}) {
  const createCategory = useCreateMarketCategory();

  const [name, setName] = useState('');
  const [slug, setSlug] = useState('');
  const [isSlugTouched, setIsSlugTouched] = useState(false);

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
  }

  function handleClose() {
    reset();
    onClose();
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    try {
      const result = await createCategory.mutateAsync({ name, slug });
      reset();
      if (onSuccess && result) {
        onSuccess(result.id);
      }
      onClose();
    } catch (err) {
      // Error handled by mutation
    }
  }

  return (
    <Modal open={open} onClose={handleClose} title="Create Category">
      <form onSubmit={handleSubmit}>
        <FormField label="Category Name">
          <Input required value={name} onChange={handleNameChange} placeholder="e.g. Matka" />
        </FormField>
        <FormField label="Slug (unique, URL-safe)">
          <Input required value={slug} onChange={(e) => { setSlug(e.target.value); setIsSlugTouched(true); }} placeholder="e.g. matka" />
        </FormField>

        {createCategory.isError && <p className="mb-3 text-xs text-red-600">{(createCategory.error as Error).message}</p>}

        <div className="mt-4 flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={handleClose}>
            Cancel
          </Button>
          <Button type="submit" loading={createCategory.isPending}>
            Create Category
          </Button>
        </div>
      </form>
    </Modal>
  );
}
