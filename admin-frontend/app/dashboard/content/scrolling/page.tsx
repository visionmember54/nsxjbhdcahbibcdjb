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
import { useScrollingMessages, useCreateScrollingMessage, useUpdateScrollingMessage, useDeleteScrollingMessage } from '@/hooks/useContent';

export default function ScrollingMessagesPage() {
  const { data: messages, isLoading, isError, error } = useScrollingMessages();
  const createMessage = useCreateScrollingMessage();
  const updateMessage = useUpdateScrollingMessage();
  const confirm = useConfirm();
  const deleteMessage = useDeleteScrollingMessage();
  const [open, setOpen] = useState(false);

  return (
    <div>
      <PageHeader
        icon="file"
        title="Scrolling Messages"
        description="The homepage marquee ticker."
        action={<Button onClick={() => setOpen(true)}>+ New message</Button>}
      />
      <Card>
        {isLoading && <LoadingState />}
        {isError && <ErrorState message={(error as Error).message} />}
        {messages && messages.length === 0 && <EmptyState title="No messages yet" />}

        {messages && messages.length > 0 && (
          <Table>
            <THead>
              <Tr>
                <Th>Text</Th>
                <Th>Order</Th>
                <Th>Status</Th>
                <Th></Th>
              </Tr>
            </THead>
            <TBody>
              {messages.map((m) => (
                <Tr key={m.id}>
                  <Td className="max-w-md">{m.text}</Td>
                  <Td>{m.display_order}</Td>
                  <Td>
                    <Badge tone={m.enabled ? 'green' : 'slate'}>{m.enabled ? 'Enabled' : 'Disabled'}</Badge>
                  </Td>
                  <Td className="space-x-3">
                    <button
                      className="text-xs font-semibold text-brand-600 hover:underline"
                      onClick={() => updateMessage.mutate({ id: m.id, enabled: !m.enabled })}
                    >
                      {m.enabled ? 'Disable' : 'Enable'}
                    </button>
                    <button
                      className="text-xs font-semibold text-red-600 hover:underline"
                      onClick={async () => (await confirm('Delete this message?')) && deleteMessage.mutate(m.id)}
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

      <Modal open={open} onClose={() => setOpen(false)} title="New scrolling message">
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            const form = new FormData(e.currentTarget as HTMLFormElement);
            await createMessage.mutateAsync({
              text: String(form.get('text') || ''),
              display_order: Number(form.get('display_order') || 0),
            });
            setOpen(false);
          }}
        >
          <FormField label="Text">
            <Input name="text" required />
          </FormField>
          <FormField label="Display order">
            <Input name="display_order" type="number" defaultValue={0} />
          </FormField>
          {createMessage.isError && <p className="mb-2 text-xs text-red-600">{(createMessage.error as Error).message}</p>}
          <Button type="submit" loading={createMessage.isPending} className="w-full">
            Create
          </Button>
        </form>
      </Modal>
    </div>
  );
}
