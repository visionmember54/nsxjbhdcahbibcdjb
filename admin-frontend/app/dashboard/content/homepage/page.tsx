'use client';

import Link from 'next/link';
import PageHeader from '@/components/layout/PageHeader';
import { Card, CardBody, CardHeader, CardTitle } from '@/components/ui/Card';
import { LoadingState, EmptyState } from '@/components/ui/States';
import { FormField, Input } from '@/components/ui/Field';
import Button from '@/components/ui/Button';
import { useBanners, useScrollingMessages, useSiteSettings, useUpdateSiteSetting } from '@/hooks/useContent';
import { useEffect, useState } from 'react';

export default function HomepagePage() {
  const { data: banners, isLoading: bannersLoading } = useBanners();
  const { data: messages, isLoading: messagesLoading } = useScrollingMessages();
  const { data: settings } = useSiteSettings();
  const updateSetting = useUpdateSiteSetting();
  const heroImage = settings?.find((s) => s.key === 'hero_image_url')?.value ?? '';
  const [heroValue, setHeroValue] = useState(heroImage);

  // settings load async after mount -- resync the draft once real data arrives.
  useEffect(() => setHeroValue(heroImage), [heroImage]);

  return (
    <div>
      <PageHeader icon="file" title="Homepage" description="Everything a user sees on first launch." />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Hero image</CardTitle>
          </CardHeader>
          <CardBody>
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                await updateSetting.mutateAsync({ key: 'hero_image_url', value: heroValue });
              }}
            >
              <FormField label="Hero image URL">
                <Input value={heroValue} onChange={(e) => setHeroValue(e.target.value)} placeholder="https://…" />
              </FormField>
              <Button type="submit" loading={updateSetting.isPending} size="sm">
                Save
              </Button>
            </form>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Featured Markets</CardTitle>
          </CardHeader>
          <CardBody>
            <p className="text-sm text-slate-500">
              Markets are featured by their <code className="rounded bg-slate-100 px-1">display_order</code> — manage this from{' '}
              <Link href="/dashboard/markets" className="text-brand-600 hover:underline">
                All Markets
              </Link>
              .
            </p>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Banners</CardTitle>
          </CardHeader>
          <CardBody>
            {bannersLoading && <LoadingState />}
            {banners && banners.length === 0 && <EmptyState title="No banners configured" />}
            {banners && banners.length > 0 && (
              <ul className="space-y-2 text-sm">
                {banners.map((b) => (
                  <li key={b.id} className="flex items-center justify-between rounded-lg border border-slate-100 px-3 py-2">
                    <span>{b.title || '(untitled)'}</span>
                    <span className={b.enabled ? 'text-emerald-600' : 'text-slate-400'}>{b.enabled ? 'Live' : 'Hidden'}</span>
                  </li>
                ))}
              </ul>
            )}
            <Link href="/dashboard/content/banners" className="mt-3 inline-block text-xs font-semibold text-brand-600 hover:underline">
              Manage banners →
            </Link>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Scrolling Messages</CardTitle>
          </CardHeader>
          <CardBody>
            {messagesLoading && <LoadingState />}
            {messages && messages.length === 0 && <EmptyState title="No scrolling messages configured" />}
            {messages && messages.length > 0 && (
              <ul className="space-y-2 text-sm">
                {messages.map((m) => (
                  <li key={m.id} className="rounded-lg border border-slate-100 px-3 py-2">
                    {m.text}
                  </li>
                ))}
              </ul>
            )}
            <Link href="/dashboard/content/scrolling" className="mt-3 inline-block text-xs font-semibold text-brand-600 hover:underline">
              Manage messages →
            </Link>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
