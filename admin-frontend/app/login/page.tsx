'use client';

import { FormEvent, useEffect, useState } from 'react';
import { useLogin } from '@/hooks/useAuth';
import Button from '@/components/ui/Button';
import { FormField, Input } from '@/components/ui/Field';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [expired, setExpired] = useState(false);
  const login = useLogin();

  useEffect(() => {
    setExpired(new URLSearchParams(window.location.search).get('expired') === '1');
  }, []);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    login.mutate({ email, password });
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-ink-950 px-4">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute inset-0 bg-gradient-to-br from-brand-950 via-ink-950 to-ink-900" />
        <div className="absolute -left-32 -top-32 h-96 w-96 rounded-full bg-brand-500/20 blur-3xl" />
        <div className="absolute -bottom-40 -right-24 h-[28rem] w-[28rem] rounded-full bg-brand-400/10 blur-3xl" />
        <div
          className="absolute inset-0 opacity-[0.07]"
          style={{ backgroundImage: 'radial-gradient(circle, #ffffff 1px, transparent 1px)', backgroundSize: '28px 28px' }}
        />
      </div>

      <div className="relative w-full max-w-sm">
        <div className="mb-7 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-400 to-brand-600 text-2xl font-bold text-white shadow-glow">
            K
          </div>
          <h1 className="text-xl font-bold tracking-tight text-white">Kalyan Admin</h1>
          <p className="mt-1.5 text-xs text-brand-200/80">Operations console for markets, results, and virtual credits</p>
        </div>

        <form onSubmit={handleSubmit} className="rounded-2xl bg-white/95 p-6 shadow-2xl ring-1 ring-white/10 backdrop-blur">
          <h2 className="mb-5 text-base font-semibold tracking-tight text-slate-900">Sign in to continue</h2>

          <FormField label="Email">
            <Input
              type="email"
              required
              autoFocus
              maxLength={254}
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
            />
          </FormField>

          <FormField label="Password">
            <div className="relative">
              <Input
                type={showPassword ? 'text' : 'password'}
                required
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="pr-16"
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                aria-pressed={showPassword}
                className="absolute inset-y-0 right-0 px-3 text-xs font-semibold text-slate-500 hover:text-slate-800"
              >
                {showPassword ? 'Hide' : 'Show'}
              </button>
            </div>
          </FormField>

          {expired && !login.isError && (
            <p role="status" className="mb-3 rounded-lg bg-amber-50 px-3 py-2 text-xs font-medium text-amber-800">
              Your session expired. Please sign in again.
            </p>
          )}

          {login.isError && (
            <p role="alert" className="mb-3 rounded-lg bg-red-50 px-3 py-2 text-xs font-medium text-red-700">{(login.error as Error).message}</p>
          )}

          <Button type="submit" className="w-full" loading={login.isPending}>
            Sign in
          </Button>
        </form>

        <p className="mt-5 text-center text-xs text-brand-300/70">
          Admin access only. Virtual Learning Credits &mdash; no real-money transactions.
        </p>
      </div>
    </div>
  );
}
