import { NextRequest, NextResponse } from 'next/server';
import { getBackendUrl } from '@/lib/backend-url';
import { isSameOrigin } from '@/lib/security';

const BACKEND_URL = getBackendUrl();
const SESSION_COOKIE = process.env.SESSION_COOKIE_NAME || 'kalyan_admin_session';

export async function POST(req: NextRequest) {
  if (!isSameOrigin(req)) return NextResponse.json({ detail: 'Cross-origin request blocked' }, { status: 403 });

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ detail: 'Invalid request' }, { status: 400 });
  }

  let backendResponse: Response;
  try {
    backendResponse = await fetch(`${BACKEND_URL}/admin/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(20_000),
    });
  } catch {
    return NextResponse.json(
      { detail: 'Could not reach the server. It may be starting up — please try again in a moment.' },
      { status: 503 },
    );
  }

  const text = await backendResponse.text();
  let data: any;
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    // Backend returned something non-JSON (rate-limit plain text, a gateway
    // HTML error page during cold start, etc.) -- surface a clean error
    // instead of letting JSON.parse crash the route into an opaque 500.
    return NextResponse.json(
      { detail: 'Backend is temporarily unavailable. Please try again in a moment.' },
      { status: 503 },
    );
  }

  if (!backendResponse.ok) {
    return NextResponse.json(data, { status: backendResponse.status });
  }

  const response = NextResponse.json({ user: data.user });
  response.cookies.set(SESSION_COOKIE, data.token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    path: '/',
    maxAge: 60 * 60 * 8,
  });
  return response;
}

export async function DELETE(req: NextRequest) {
  if (!isSameOrigin(req)) return NextResponse.json({ detail: 'Cross-origin request blocked' }, { status: 403 });

  // Revoke the token server-side (best effort) so a copied cookie stops working.
  const token = req.cookies.get(SESSION_COOKIE)?.value;
  if (token) {
    await fetch(`${BACKEND_URL}/admin/auth/logout`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      signal: AbortSignal.timeout(5_000),
    }).catch(() => {});
  }
  const response = NextResponse.json({ ok: true });
  response.cookies.delete(SESSION_COOKIE);
  return response;
}
