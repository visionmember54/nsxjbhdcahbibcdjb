'use client';

import { useEffect, useState } from 'react';
import PageHeader from '@/components/layout/PageHeader';
import { Card, CardBody, CardHeader, CardTitle } from '@/components/ui/Card';
import { FormField, Input, Textarea } from '@/components/ui/Field';
import Button from '@/components/ui/Button';
import { LoadingState } from '@/components/ui/States';
import { useSiteSettings, useUpdateSiteSetting } from '@/hooks/useContent';

const TEXT_FIELDS: { key: string; label: string; placeholder: string }[] = [
  { key: 'payment_upi_id', label: 'UPI ID', placeholder: 'e.g. kalyanmerchant@icici' },
  { key: 'payment_merchant_name', label: 'Merchant name', placeholder: 'e.g. Kalyan Milan' },
];

const NUMBER_FIELDS: { key: string; label: string; placeholder: string }[] = [
  { key: 'payment_min_deposit', label: 'Minimum deposit (₹)', placeholder: '300' },
  { key: 'payment_max_deposit', label: 'Maximum deposit (₹)', placeholder: '100000' },
  { key: 'payment_min_withdrawal', label: 'Minimum withdrawal (₹)', placeholder: '1000' },
];

const ALL_KEYS = [...TEXT_FIELDS, ...NUMBER_FIELDS, { key: 'payment_instructions', label: '', placeholder: '' }];

export default function PaymentSettingsPage() {
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
      <PageHeader
        icon="coin"
        title="Payment Settings"
        description="UPI ID, QR code, and deposit/withdrawal limits shown to users in the app's Add Points screen."
      />
      <Card>
        <CardHeader>
          <CardTitle subtitle="Saved to site settings, read live by the app's /wallet/payment-config endpoint">
            UPI &amp; deposit configuration
          </CardTitle>
        </CardHeader>
        <CardBody>
          {isLoading && <LoadingState />}
          {!isLoading && (
            <form
              className="grid gap-4"
              onSubmit={async (e) => {
                e.preventDefault();
                await Promise.all(ALL_KEYS.map((f) => updateSetting.mutateAsync({ key: f.key, value: values[f.key] ?? '' })));
              }}
            >
              <div className="grid gap-4 sm:grid-cols-2">
                {TEXT_FIELDS.map((f) => (
                  <FormField key={f.key} label={f.label}>
                    <Input
                      value={values[f.key] ?? ''}
                      onChange={(e) => setValues((prev) => ({ ...prev, [f.key]: e.target.value }))}
                      placeholder={f.placeholder}
                    />
                  </FormField>
                ))}
              </div>

              <div className="grid gap-4 sm:grid-cols-3">
                {NUMBER_FIELDS.map((f) => (
                  <FormField key={f.key} label={f.label}>
                    <Input
                      type="number"
                      min={0}
                      value={values[f.key] ?? ''}
                      onChange={(e) => setValues((prev) => ({ ...prev, [f.key]: e.target.value }))}
                      placeholder={f.placeholder}
                    />
                  </FormField>
                ))}
              </div>

              <FormField label="Deposit instructions (shown below the QR code)">
                <Textarea
                  rows={4}
                  value={values.payment_instructions ?? ''}
                  onChange={(e) => setValues((prev) => ({ ...prev, payment_instructions: e.target.value }))}
                  placeholder="1. Pay using UPI to the UPI ID or scan QR.&#10;2. Note down the 12-digit UTR number.&#10;3. Enter amount and UTR below."
                />
              </FormField>

              <div>
                {updateSetting.isSuccess && <p className="mb-2 text-xs text-emerald-600">Saved. The app will pick this up on its next request.</p>}
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
