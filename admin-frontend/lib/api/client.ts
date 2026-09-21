export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`/api/backend${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
  });

  if (res.status === 401 && typeof window !== 'undefined') {
    if (window.location.pathname !== '/login') {
      const from = encodeURIComponent(window.location.pathname + window.location.search);
      window.location.href = `/login?expired=1&from=${from}`;
    }
    throw new ApiError(401, 'Unauthorized');
  }

  const text = await res.text();
  let data: any = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      throw new ApiError(res.status || 502, 'Server is temporarily unavailable. Please try again.');
    }
  }

  if (!res.ok) {
    const message = (data && (data.detail || data.error?.message || data.message)) || `Request failed (${res.status})`;
    throw new ApiError(res.status, typeof message === 'string' ? message : JSON.stringify(message));
  }

  return data as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path, { method: 'GET' }),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'POST', body: body !== undefined ? JSON.stringify(body) : undefined }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PATCH', body: body !== undefined ? JSON.stringify(body) : undefined }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PUT', body: body !== undefined ? JSON.stringify(body) : undefined }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
};
