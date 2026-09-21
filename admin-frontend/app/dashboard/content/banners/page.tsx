'use client';

import { useConfirm } from '@/components/ui/Feedback';
import { useState } from 'react';
import PageHeader from '@/components/layout/PageHeader';
import { Card } from '@/components/ui/Card';
import { Table, TBody, Td, Th, THead, Tr } from '@/components/ui/Table';
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/States';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';
import { FormField, Input } from '@/components/ui/Field';
import { useBanners, useCreateBanner, useUpdateBanner, useDeleteBanner } from '@/hooks/useContent';

export default function BannersPage() {
  const { data: banners, isLoading, isError, error } = useBanners();
  const createBanner = useCreateBanner();
  const updateBanner = useUpdateBanner();
  const confirm = useConfirm();
  const deleteBanner = useDeleteBanner();
  const [open, setOpen] = useState(false);

  return (
    <div>
      <PageHeader icon="file" title="Banners" description="Homepage hero banners, in display order." action={<Button onClick={() => setOpen(true)}>+ New banner</Button>} />
      <Card>
        {isLoading && <LoadingState />}
        {isError && <ErrorState message={(error as Error).message} />}
        {banners && banners.length === 0 && <EmptyState title="No banners yet" />}

        {banners && banners.length > 0 && (
          <Table>
            <THead>
              <Tr>
                <Th>Title</Th>
                <Th>Image URL</Th>
                <Th>Link</Th>
                <Th>Order</Th>
                <Th>Status</Th>
                <Th></Th>
              </Tr>
            </THead>
            <TBody>
              {banners.map((b) => (
                <Tr key={b.id}>
                  <Td className="font-medium text-slate-900">{b.title || '—'}</Td>
                  <Td className="max-w-xs truncate">{b.image_url || '—'}</Td>
                  <Td className="max-w-xs truncate">{b.link || '—'}</Td>
                  <Td>{b.display_order}</Td>
                  <Td>
                    <Badge tone={b.enabled ? 'green' : 'slate'}>{b.enabled ? 'Enabled' : 'Disabled'}</Badge>
                  </Td>
                  <Td className="space-x-3">
                    <button
                      className="text-xs font-semibold text-brand-600 hover:underline"
                      onClick={() => updateBanner.mutate({ id: b.id, enabled: !b.enabled })}
                    >
                      {b.enabled ? 'Disable' : 'Enable'}
                    </button>
                    <button
                      className="text-xs font-semibold text-red-600 hover:underline"
                      onClick={async () => (await confirm('Delete this banner?')) && deleteBanner.mutate(b.id)}
                    >
                      Delete
                    </button>
                  </Td>
                </Tr>
              ))}
            </TBody>
          </Table>
        )}
      </Card>

      <Modal open={open} onClose={() => setOpen(false)} title="New banner">
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            const form = new FormData(e.currentTarget as HTMLFormElement);
            await createBanner.mutateAsync({
              title: String(form.get('title') || ''),
              image_url: String(form.get('image_url') || ''),
              link: String(form.get('link') || ''),
              display_order: Number(form.get('display_order') || 0),
            });
            setOpen(false);
          }}
        >
          <FormField label="Title">
            <Input name="title" />
          </FormField>
          <FormField label="Image URL">
            <Input name="image_url" placeholder="https://…" />
          </FormField>
          <FormField label="Link">
            <Input name="link" placeholder="https://… (optional)" />
          </FormField>
          <FormField label="Display order">
            <Input name="display_order" type="number" defaultValue={0} />
          </FormField>
          {createBanner.isError && <p className="mb-2 text-xs text-red-600">{(createBanner.error as Error).message}</p>}
          <Button type="submit" loading={createBanner.isPending} className="w-full">
            Create
          </Button>
        </form>
      </Modal>
    </div>
  );
}
