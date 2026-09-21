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
import { FormField, Input, Textarea } from '@/components/ui/Field';
import { useFaqs, useCreateFaq, useUpdateFaq, useDeleteFaq } from '@/hooks/useContent';

export default function FaqPage() {
  const { data: faqs, isLoading, isError, error } = useFaqs();
  const createFaq = useCreateFaq();
  const updateFaq = useUpdateFaq();
  const confirm = useConfirm();
  const deleteFaq = useDeleteFaq();
  const [open, setOpen] = useState(false);

  return (
    <div>
      <PageHeader icon="support" title="FAQ" description="Frequently asked questions shown to users." action={<Button onClick={() => setOpen(true)}>+ New FAQ</Button>} />
      <Card>
        {isLoading && <LoadingState />}
        {isError && <ErrorState message={(error as Error).message} />}
        {faqs && faqs.length === 0 && <EmptyState title="No FAQs yet" />}

        {faqs && faqs.length > 0 && (
          <Table>
            <THead>
              <Tr>
                <Th>Question</Th>
                <Th>Answer</Th>
                <Th>Status</Th>
                <Th></Th>
              </Tr>
            </THead>
            <TBody>
              {faqs.map((f) => (
                <Tr key={f.id}>
                  <Td className="max-w-xs font-medium text-slate-900">{f.question}</Td>
                  <Td className="max-w-md truncate">{f.answer}</Td>
                  <Td>
                    <Badge tone={f.enabled ? 'green' : 'slate'}>{f.enabled ? 'Enabled' : 'Disabled'}</Badge>
                  </Td>
                  <Td className="space-x-3">
                    <button
                      className="text-xs font-semibold text-brand-600 hover:underline"
                      onClick={() => updateFaq.mutate({ id: f.id, enabled: !f.enabled })}
                    >
                      {f.enabled ? 'Disable' : 'Enable'}
                    </button>
                    <button
                      className="text-xs font-semibold text-red-600 hover:underline"
                      onClick={async () => (await confirm('Delete this FAQ?')) && deleteFaq.mutate(f.id)}
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

      <Modal open={open} onClose={() => setOpen(false)} title="New FAQ">
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            const form = new FormData(e.currentTarget as HTMLFormElement);
            await createFaq.mutateAsync({
              question: String(form.get('question') || ''),
              answer: String(form.get('answer') || ''),
              display_order: Number(form.get('display_order') || 0),
            });
            setOpen(false);
          }}
        >
          <FormField label="Question">
            <Input name="question" required />
          </FormField>
          <FormField label="Answer">
            <Textarea name="answer" rows={3} required />
          </FormField>
          <FormField label="Display order">
            <Input name="display_order" type="number" defaultValue={0} />
          </FormField>
          {createFaq.isError && <p className="mb-2 text-xs text-red-600">{(createFaq.error as Error).message}</p>}
          <Button type="submit" loading={createFaq.isPending} className="w-full">
            Create
          </Button>
        </form>
      </Modal>
    </div>
  );
}
