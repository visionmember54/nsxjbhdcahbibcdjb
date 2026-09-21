'use client';

import { useEffect, useState } from 'react';
import PageHeader from '@/components/layout/PageHeader';
import { Card, CardBody, CardHeader, CardTitle } from '@/components/ui/Card';
import { FormField, Input } from '@/components/ui/Field';
import Button from '@/components/ui/Button';
import { LoadingState } from '@/components/ui/States';
import { Icon, type IconKey } from '@/components/layout/icons';
import { useSiteSettings, useUpdateSiteSetting } from '@/hooks/useContent';

const FIELDS: { key: string; label: string; placeholder: string; icon: IconKey }[] = [
  { key: 'support_phone', label: 'Support phone', placeholder: 'e.g. +91 7000000000', icon: 'support' },
  { key: 'support_whatsapp', label: 'WhatsApp number', placeholder: 'e.g. 917000000000', icon: 'support' },
  { key: 'support_telegram', label: 'Telegram link', placeholder: 'e.g. https://t.me/yourchannel', icon: 'support' },
  { key: 'support_email', label: 'Support email', placeholder: 'e.g. support@example.com', icon: 'file' },
  { key: 'app_share_url', label: 'App share link', placeholder: 'e.g. https://example.com', icon: 'chart' },
];

export default function ContactSupportPage() {
  const { data: settings, isLoading } = useSiteSettings();
  const updateSetting = useUpdateSiteSetting();
  const [values, setValues] = useState<Record<string, string>>({});

  useEffect(() => {
    if (settings) {
      const map: Record<string, string> = {};
      settings.forEach((s) => (map[s.key] = s.value));
      setValues(map);
    }
  }, [settings]);

  return (
    <div>
      <PageHeader icon="support" title="Contact & WhatsApp" description="Support contact links shown to users in the app and on the homepage." />
      <Card>
        <CardHeader>
          <CardTitle subtitle="Saved to site settings, read by the app's /support endpoint">Contact settings</CardTitle>
        </CardHeader>
        <CardBody>
          {isLoading && <LoadingState />}
          {!isLoading && (
            <form
              className="grid gap-4 sm:grid-cols-2"
              onSubmit={async (e) => {
                e.preventDefault();
                await Promise.all(FIELDS.map((f) => updateSetting.mutateAsync({ key: f.key, value: values[f.key] ?? '' })));
              }}
            >
              {FIELDS.map((f) => (
                <FormField key={f.key} label={f.label}>
                  <div className="flex items-center gap-2">
                    <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
                      <Icon name={f.icon} className="h-4 w-4" />
                    </span>
                    <Input
                      value={values[f.key] ?? ''}
                      onChange={(e) => setValues((prev) => ({ ...prev, [f.key]: e.target.value }))}
                      placeholder={f.placeholder}
                    />
                  </div>
                </FormField>
              ))}
              <div className="sm:col-span-2">
                {updateSetting.isSuccess && <p className="mb-2 text-xs text-emerald-600">Saved.</p>}
                <Button type="submit" loading={updateSetting.isPending}>
                  Save all
                </Button>
              </div>
            </form>
          )}
        </CardBody>
      </Card>
    </div>
  );
}
