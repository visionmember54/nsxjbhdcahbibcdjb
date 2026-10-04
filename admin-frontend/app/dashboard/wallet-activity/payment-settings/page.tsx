'use client';

import { useEffect, useState } from 'react';
import PageHeader from '@/components/layout/PageHeader';
import { Card, CardBody, CardHeader, CardTitle } from '@/components/ui/Card';
import { FormField, Input, Textarea } from '@/components/ui/Field';
import Button from '@/components/ui/Button';
import { LoadingState } from '@/components/ui/States';
import { useSiteSettings, useSendPaymentSettingsOtp, useUpdatePaymentSettingsBulk } from '@/hooks/useContent';

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
  const sendOtp = useSendPaymentSettingsOtp();
  const updateBulk = useUpdatePaymentSettingsBulk();
  const [values, setValues] = useState<Record<string, string>>({});
  const [otpSessionId, setOtpSessionId] = useState<string | null>(null);
  const [otpCode, setOtpCode] = useState('');
  const [saved, setSaved] = useState(false);

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
          <CardTitle subtitle="Saved to site settings, read live by the app's /wallet/payment-config endpoint. Changing these requires an OTP sent to your own admin phone, to confirm it's really you.">
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
                setSaved(false);
                if (!otpSessionId) {
                  const resp = await sendOtp.mutateAsync();
                  setOtpSessionId(resp.otpSessionId);
                  return;
                }
                const toSave = Object.fromEntries(ALL_KEYS.map((f) => [f.key, values[f.key] ?? '']));
                await updateBulk.mutateAsync({ values: toSave, otp_session_id: otpSessionId, otp_code: otpCode });
                setOtpSessionId(null);
                setOtpCode('');
                setSaved(true);
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

              {otpSessionId && (
                <FormField label="Enter the OTP sent to your admin phone">
                  <Input value={otpCode} onChange={(e) => setOtpCode(e.target.value)} placeholder="6-digit code" maxLength={10} autoFocus />
                </FormField>
              )}

              <div>
                {saved && <p className="mb-2 text-xs text-emerald-600">Saved. The app will pick this up on its next request.</p>}
                {sendOtp.isError && <p className="mb-2 text-xs text-red-600">{(sendOtp.error as Error).message}</p>}
                {updateBulk.isError && <p className="mb-2 text-xs text-red-600">{(updateBulk.error as Error).message}</p>}
                <div className="flex items-center gap-3">
                  <Button type="submit" loading={sendOtp.isPending || updateBulk.isPending} disabled={!!otpSessionId && !otpCode}>
                    {otpSessionId ? 'Confirm & save' : 'Send OTP to save'}
                  </Button>
                  {otpSessionId && (
                    <button
                      type="button"
                      className="text-xs font-semibold text-slate-500 hover:underline"
                      onClick={() => {
                        setOtpSessionId(null);
                        setOtpCode('');
                      }}
                    >
                      Cancel
                    </button>
                  )}
                </div>
              </div>
            </form>
          )}
        </CardBody>
      </Card>
    </div>
  );
}
