import { cookies } from 'next/headers';
import { NextRequest, NextResponse } from 'next/server';
import { getBackendUrl } from '@/lib/backend-url';
import { isSameOrigin } from '@/lib/security';

const BACKEND_URL = getBackendUrl();
const SESSION_COOKIE = process.env.SESSION_COOKIE_NAME || 'kalyan_admin_session';
const TIMEOUT_MS = 20_000;

function fail(status: number, detail: string) {
  return NextResponse.json({ detail }, { status });
}

async function proxy(req: NextRequest, path: string[]): Promise<NextResponse> {
  const mutating = req.method !== 'GET' && req.method !== 'HEAD';
  if (mutating && !isSameOrigin(req)) return fail(403, 'Cross-origin request blocked');
  if (path.some((s) => !s || s === '.' || s === '..')) return fail(400, 'Invalid path');

  const token = cookies().get(SESSION_COOKIE)?.value;
  const url = `${BACKEND_URL}/${path.map(encodeURIComponent).join('/')}${req.nextUrl.search}`;

  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const init: RequestInit = { method: req.method, headers, signal: AbortSignal.timeout(TIMEOUT_MS) };
  if (mutating) {
    const body = await req.text();
    if (body) init.body = body;
  }

  try {
    const res = await fetch(url, init);
    const out: Record<string, string> = { 'Content-Type': res.headers.get('Content-Type') || 'application/json' };
    const disposition = res.headers.get('Content-Disposition');
    if (disposition) out['Content-Disposition'] = disposition;
    // arrayBuffer keeps binary downloads (CSV/PDF) intact.
    return new NextResponse(await res.arrayBuffer(), { status: res.status, headers: out });
  } catch (e) {
    const timedOut = e instanceof Error && (e.name === 'TimeoutError' || e.name === 'AbortError');
    return timedOut
      ? fail(504, 'The server took too long to respond. Please try again.')
      : fail(502, 'Could not reach the server. Please try again in a moment.');
  }
}

type RouteParams = { params: { path: string[] } };

export async function GET(req: NextRequest, { params }: RouteParams) {
  return proxy(req, params.path);
}
export async function POST(req: NextRequest, { params }: RouteParams) {
  return proxy(req, params.path);
}
export async function PATCH(req: NextRequest, { params }: RouteParams) {
  return proxy(req, params.path);
}
export async function PUT(req: NextRequest, { params }: RouteParams) {
  return proxy(req, params.path);
}
export async function DELETE(req: NextRequest, { params }: RouteParams) {
  return proxy(req, params.path);
}
