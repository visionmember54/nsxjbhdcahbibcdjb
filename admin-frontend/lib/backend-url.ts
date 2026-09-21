export function getBackendUrl(): string {
  const raw = process.env.BACKEND_URL || 'http://localhost:8000';
  return /^https?:\/\//.test(raw) ? raw : `https://${raw}`;
}
