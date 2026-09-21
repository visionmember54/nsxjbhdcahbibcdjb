'use client';

import { useConfirm } from '@/components/ui/Feedback';
import { useState } from 'react';
import PageHeader from '@/components/layout/PageHeader';
import { Card } from '@/components/ui/Card';
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/States';
import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';
import { FormField, Input, Select, Textarea } from '@/components/ui/Field';
import { EducationalContent } from '@/lib/api/types';
import { useEducationalContent, useCreateEducationalContent, useUpdateEducationalContent, useDeleteEducationalContent } from '@/hooks/useContent';
import { useGameTypes } from '@/hooks/useGameTypes';

export default function EducationalContentPage() {
  const { data: content, isLoading, isError, error } = useEducationalContent();
  const { data: gameTypes } = useGameTypes();
  const createContent = useCreateEducationalContent();
  const updateContent = useUpdateEducationalContent();
  const confirm = useConfirm();
  const deleteContent = useDeleteEducationalContent();
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<EducationalContent | null>(null);

  return (
    <div>
      <PageHeader
        icon="file"
        title="Game Rules & Educational Content"
        description="How each game works, examples, and probability explanations — shown to users."
        action={<Button onClick={() => setOpen(true)}>+ New entry</Button>}
      />

      {isLoading && <LoadingState />}
      {isError && <ErrorState message={(error as Error).message} />}
      {content && content.length === 0 && <EmptyState title="No educational content yet" />}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {content?.map((c) => (
          <Card key={c.id}>
            <div className="p-5">
              <h3 className="text-sm font-bold text-slate-900">{c.title}</h3>
              {c.description && <p className="mt-1 text-sm text-slate-600">{c.description}</p>}
              {c.example && (
                <p className="mt-2 text-xs text-slate-500">
                  <span className="font-semibold">Example:</span> {c.example}
                </p>
              )}
              {c.probability_explanation && (
                <p className="mt-1 text-xs text-slate-500">
                  <span className="font-semibold">Probability:</span> {c.probability_explanation}
                </p>
              )}
              {c.rules && (
                <p className="mt-1 text-xs text-slate-500">
                  <span className="font-semibold">Rules:</span> {c.rules}
                </p>
              )}
              <div className="mt-4 flex gap-3"><button className="text-xs font-semibold text-brand-600 hover:underline" onClick={() => setEditing(c)}>Edit</button><button className="text-xs font-semibold text-red-600 hover:underline" onClick={async () => { if (await confirm(`Delete ${c.title}?`)) deleteContent.mutate(c.id); }}>Delete</button></div>
            </div>
          </Card>
        ))}
      </div>

      <Modal open={open} onClose={() => setOpen(false)} title="New educational content" maxWidth="max-w-2xl">
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            const form = new FormData(e.currentTarget as HTMLFormElement);
            const gameTypeId = form.get('game_type_id');
            await createContent.mutateAsync({
              game_type_id: gameTypeId ? Number(gameTypeId) : null,
              title: String(form.get('title') || ''),
              description: String(form.get('description') || ''),
              how_it_works: String(form.get('how_it_works') || ''),
              example: String(form.get('example') || ''),
              probability_explanation: String(form.get('probability_explanation') || ''),
              rules: String(form.get('rules') || ''),
            });
            setOpen(false);
          }}
        >
          <div className="grid grid-cols-2 gap-3">
            <FormField label="Title">
              <Input name="title" required />
            </FormField>
            <FormField label="Game type (optional)">
              <Select name="game_type_id" defaultValue="">
                <option value="">— General —</option>
                {gameTypes?.map((gt) => (
                  <option key={gt.id} value={gt.id}>
                    {gt.code}
                  </option>
                ))}
              </Select>
            </FormField>
          </div>
          <FormField label="Description">
            <Textarea name="description" rows={2} />
          </FormField>
          <FormField label="How it works">
            <Textarea name="how_it_works" rows={2} />
          </FormField>
          <FormField label="Example">
            <Input name="example" placeholder="e.g. 112" />
          </FormField>
          <FormField label="Probability explanation">
            <Textarea name="probability_explanation" rows={2} />
          </FormField>
          <FormField label="Rules">
            <Textarea name="rules" rows={2} />
          </FormField>
          {createContent.isError && <p className="mb-2 text-xs text-red-600">{(createContent.error as Error).message}</p>}
          <Button type="submit" loading={createContent.isPending} className="w-full">
            Save
          </Button>
        </form>
      </Modal>

      <Modal open={editing !== null} onClose={() => setEditing(null)} title="Edit educational content" maxWidth="max-w-2xl">
        {editing && <form key={editing.id} onSubmit={async (e) => { e.preventDefault(); const form = new FormData(e.currentTarget); const rawGameType = form.get('game_type_id'); await updateContent.mutateAsync({ id: editing.id, game_type_id: rawGameType ? Number(rawGameType) : null, title: String(form.get('title') || ''), description: String(form.get('description') || ''), how_it_works: String(form.get('how_it_works') || ''), example: String(form.get('example') || ''), probability_explanation: String(form.get('probability_explanation') || ''), rules: String(form.get('rules') || '') }); setEditing(null); }}>
          <div className="grid grid-cols-2 gap-3"><FormField label="Title"><Input name="title" required defaultValue={editing.title} /></FormField><FormField label="Game type"><Select name="game_type_id" defaultValue={editing.game_type_id ?? ''}><option value="">— General —</option>{gameTypes?.map((gt) => <option key={gt.id} value={gt.id}>{gt.code}</option>)}</Select></FormField></div>
          <FormField label="Description"><Textarea name="description" rows={2} defaultValue={editing.description} /></FormField><FormField label="How it works"><Textarea name="how_it_works" rows={2} defaultValue={editing.how_it_works} /></FormField><FormField label="Example"><Input name="example" defaultValue={editing.example} /></FormField><FormField label="Probability explanation"><Textarea name="probability_explanation" rows={2} defaultValue={editing.probability_explanation} /></FormField><FormField label="Rules"><Textarea name="rules" rows={2} defaultValue={editing.rules} /></FormField>
          {updateContent.isError && <p className="mb-2 text-xs text-red-600">{(updateContent.error as Error).message}</p>}<Button type="submit" loading={updateContent.isPending} className="w-full">Save changes</Button>
        </form>}
      </Modal>
    </div>
  );
}
