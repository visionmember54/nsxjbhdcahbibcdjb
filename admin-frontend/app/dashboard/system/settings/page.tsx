'use client';

import { useState } from 'react';
import Link from 'next/link';
import PageHeader from '@/components/layout/PageHeader';
import { Card } from '@/components/ui/Card';
import { Table, TBody, Td, Th, THead, Tr } from '@/components/ui/Table';
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/States';
import Button from '@/components/ui/Button';
import { Input } from '@/components/ui/Field';
import { useSiteSettings, useUpdateSiteSetting } from '@/hooks/useContent';

export default function SystemSettingsPage() {
  const { data: settings, isLoading, isError, error } = useSiteSettings();
  const updateSetting = useUpdateSiteSetting();
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [newKey, setNewKey] = useState('');
  const [newValue, setNewValue] = useState('');

  return (
    <div>
      <PageHeader icon="cog" title="Settings" description="Raw site-wide key/value configuration." />
      <p className="-mt-4 mb-6 text-xs text-slate-500">
        Looking for WhatsApp, Telegram, or support contact info? That&rsquo;s under{' '}
        <Link href="/dashboard/support/contact" className="font-semibold text-brand-600 hover:underline">
          Support → Contact &amp; WhatsApp
        </Link>
        .
      </p>
      <Card>
        {isLoading && <LoadingState />}
        {isError && <ErrorState message={(error as Error).message} />}
        {settings && settings.length === 0 && <EmptyState title="No settings yet" />}

        {settings && settings.length > 0 && (
          <Table>
            <THead>
              <Tr>
                <Th>Key</Th>
                <Th>Value</Th>
                <Th></Th>
              </Tr>
            </THead>
            <TBody>
              {settings.map((s) => (
                <Tr key={s.key}>
                  <Td className="font-mono text-xs font-medium text-slate-900">{s.key}</Td>
                  <Td>
                    <Input
                      value={drafts[s.key] ?? s.value}
                      onChange={(e) => setDrafts((prev) => ({ ...prev, [s.key]: e.target.value }))}
                    />
                  </Td>
                  <Td>
                    <Button
                      size="sm"
                      variant="secondary"
                      loading={updateSetting.isPending}
                      onClick={() => updateSetting.mutate({ key: s.key, value: drafts[s.key] ?? s.value })}
                    >
                      Save
                    </Button>
                  </Td>
                </Tr>
              ))}
            </TBody>
          </Table>
        )}

        <div className="flex items-end gap-2 border-t border-slate-100 p-4">
          <div className="flex-1">
            <p className="mb-1 text-xs font-semibold text-slate-600">New key</p>
            <Input value={newKey} onChange={(e) => setNewKey(e.target.value)} placeholder="e.g. maintenance_mode" />
          </div>
          <div className="flex-1">
            <p className="mb-1 text-xs font-semibold text-slate-600">Value</p>
            <Input value={newValue} onChange={(e) => setNewValue(e.target.value)} />
          </div>
          <Button
            onClick={async () => {
              if (!newKey) return;
              await updateSetting.mutateAsync({ key: newKey, value: newValue });
              setNewKey('');
              setNewValue('');
            }}
          >
            Add
          </Button>
        </div>
      </Card>
    </div>
  );
}
