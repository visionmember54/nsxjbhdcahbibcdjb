import { NextRequest } from 'next/server';

/** CSRF guard: a browser-sent Origin, when present, must match our own host. */
export function isSameOrigin(req: NextRequest): boolean {
  const origin = req.headers.get('origin');
  if (!origin) return true;
  try {
    return new URL(origin).host === req.headers.get('host');
  } catch {
    return false;
  }
}

/** Only same-site absolute paths; blocks open redirects like //evil.com or /\evil.com. */
export function safeRedirectPath(from: string | null | undefined): string {
  if (from && /^\/(?![/\\])/.test(from)) return from;
  return '/dashboard';
}

export function isHttpUrl(value: string | null | undefined): value is string {
  return !!value && /^https?:\/\//i.test(value);
}
