'use client';

import { useEffect, useMemo, useState } from 'react';
import PageHeader from '@/components/layout/PageHeader';
import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/States';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import { Input, Select, Textarea } from '@/components/ui/Field';
import { Icon } from '@/components/layout/icons';
import { useSupportQueries, useReplyToQuery } from '@/hooks/useSupportQueries';
import { usePermissions } from '@/hooks/usePermissions';

const PRIORITY_TONE: Record<string, 'red' | 'amber' | 'slate'> = {
  High: 'red',
  Normal: 'slate',
  Low: 'slate',
};

const STATUS_TONE: Record<string, 'blue' | 'amber' | 'green'> = {
  Open: 'blue',
  Pending: 'amber',
  Resolved: 'green',
};

export default function SupportQueriesPage() {
  const { data, isLoading, isError, error } = useSupportQueries({ limit: 100 });
  const reply = useReplyToQuery();
  const { has } = usePermissions();
  const canReply = has('support.manage');

  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [message, setMessage] = useState('');
  const [attachmentUrl, setAttachmentUrl] = useState('');
  const [attachmentType, setAttachmentType] = useState<'image' | 'audio'>('image');
  const [statusFilter, setStatusFilter] = useState<'' | 'Open' | 'Pending' | 'Resolved'>('');

  const queries = useMemo(() => {
    const items = data?.items ?? [];
    return statusFilter ? items.filter((q) => q.status === statusFilter) : items;
  }, [data, statusFilter]);

  const selected = queries.find((q) => q.id === selectedId) ?? queries[0] ?? null;

  // Selecting a different ticket (or the list refetching) shouldn't leave a
  // half-typed reply pointed at the wrong ticket.
  useEffect(() => {
    setMessage('');
    setAttachmentUrl('');
  }, [selected?.id]);

  const openCount = (data?.items ?? []).filter((q) => q.status === 'Open').length;

  return (
    <div>
      <PageHeader
        icon="support"
        title="Support Queries"
        description="User questions and issues submitted from the app — respond here."
        action={openCount > 0 ? <Badge tone="amber">{openCount} awaiting reply</Badge> : undefined}
      />

      {isLoading && <LoadingState />}
      {isError && <ErrorState message={(error as Error).message} />}

      {!isLoading && !isError && queries.length === 0 && (
        <EmptyState title="No support queries yet" hint="They'll show up here as soon as a user reaches out." />
      )}

      {!isLoading && !isError && queries.length > 0 && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-5">
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Tickets</CardTitle>
              <div className="flex gap-1">
                {(['', 'Open', 'Pending', 'Resolved'] as const).map((s) => (
                  <button
                    key={s || 'all'}
                    onClick={() => setStatusFilter(s)}
                    className={`rounded-md px-2 py-1 text-xs font-semibold transition-colors ${
                      statusFilter === s ? 'bg-brand-600 text-white' : 'text-slate-500 hover:bg-slate-100'
                    }`}
                  >
                    {s || 'All'}
                  </button>
                ))}
              </div>
            </CardHeader>
            <div className="max-h-[32rem] divide-y divide-slate-100 overflow-y-auto">
              {queries.map((q) => (
                <button
                  key={q.id}
                  onClick={() => setSelectedId(q.id)}
                  className={`block w-full px-4 py-3 text-left transition-colors ${
                    selected?.id === q.id ? 'bg-brand-50' : 'hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="truncate text-sm font-semibold text-slate-900">{q.user}</span>
                    <Badge tone={STATUS_TONE[q.status] ?? 'slate'}>{q.status}</Badge>
                  </div>
                  <p className="mt-0.5 truncate text-xs text-slate-600">{q.subject}</p>
                  <div className="mt-1 flex items-center gap-2 text-[11px] text-slate-400">
                    <Badge tone={PRIORITY_TONE[q.priority] ?? 'slate'}>{q.priority}</Badge>
                    <span>{q.updatedAt}</span>
                  </div>
                </button>
              ))}
            </div>
          </Card>

          <Card className="lg:col-span-3">
            {!selected ? (
              <EmptyState title="Select a ticket" />
            ) : (
              <>
                <CardHeader>
                  <CardTitle subtitle={selected.subject}>{selected.user}</CardTitle>
                  <div className="flex items-center gap-2">
                    <Badge tone={PRIORITY_TONE[selected.priority] ?? 'slate'}>{selected.priority}</Badge>
                    <Badge tone={STATUS_TONE[selected.status] ?? 'slate'}>{selected.status}</Badge>
                  </div>
                </CardHeader>

                <div className="max-h-96 space-y-3 overflow-y-auto p-5">
                  {selected.messages.map((m) => (
                    <div key={m.id} className={`flex ${m.sender === 'admin' ? 'justify-end' : 'justify-start'}`}>
                      <div
                        className={`max-w-[80%] rounded-xl px-3.5 py-2.5 text-sm ${
                          m.sender === 'admin'
                            ? 'bg-gradient-to-b from-brand-500 to-brand-600 text-white'
                            : 'bg-slate-100 text-slate-800'
                        }`}
                      >
                        {m.attachmentType === 'image' && m.attachmentUrl && (
                          <a href={m.attachmentUrl} target="_blank" rel="noreferrer" className="block">
                            <img src={m.attachmentUrl} alt="Attachment" className="mb-1.5 max-h-56 w-full rounded-lg object-cover" />
                          </a>
                        )}
                        {m.attachmentType === 'audio' && m.attachmentUrl && (
                          <audio controls src={m.attachmentUrl} className="mb-1.5 w-full" />
                        )}
                        {m.text && <p>{m.text}</p>}
                        <p className={`mt-1 text-[10px] ${m.sender === 'admin' ? 'text-brand-100' : 'text-slate-400'}`}>
                          {m.sender === 'admin' ? 'You' : selected.user} · {m.time}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>

                {canReply ? (
                  <div className="border-t border-slate-100 p-4">
                    <Textarea
                      rows={2}
                      value={message}
                      onChange={(e) => setMessage(e.target.value)}
                      placeholder="Type a reply…"
                    />
                    <div className="mt-2 flex gap-2">
                      <Input
                        className="flex-1"
                        value={attachmentUrl}
                        onChange={(e) => setAttachmentUrl(e.target.value)}
                        placeholder="Optional: paste an image/voice-note URL to attach"
                      />
                      <Select className="w-28" value={attachmentType} onChange={(e) => setAttachmentType(e.target.value as 'image' | 'audio')}>
                        <option value="image">Image</option>
                        <option value="audio">Voice</option>
                      </Select>
                    </div>
                    {reply.isError && <p className="mt-2 text-xs text-red-600">{(reply.error as Error).message}</p>}
                    <Button
                      className="mt-2"
                      size="sm"
                      loading={reply.isPending}
                      disabled={!message.trim() && !attachmentUrl.trim()}
                      onClick={() => {
                        reply.mutate(
                          {
                            id: selected.id,
                            message: message.trim() || undefined,
                            attachmentUrl: attachmentUrl.trim() || undefined,
                            attachmentType: attachmentUrl.trim() ? attachmentType : undefined,
                          },
                          { onSuccess: () => { setMessage(''); setAttachmentUrl(''); } }
                        );
                      }}
                    >
                      <Icon name="check" className="h-3.5 w-3.5" />
                      Send reply
                    </Button>
                  </div>
                ) : (
                  <p className="border-t border-slate-100 p-4 text-xs text-slate-400">
                    You don&rsquo;t have permission to reply to support queries.
                  </p>
                )}
              </>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}
