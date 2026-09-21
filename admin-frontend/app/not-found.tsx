import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-3 bg-slate-50 px-4 text-center">
      <h1 className="text-lg font-semibold text-slate-900">Page not found</h1>
      <p className="text-sm text-slate-500">The page you’re looking for doesn’t exist or was moved.</p>
      <Link href="/dashboard" className="text-sm font-semibold text-brand-600 hover:underline">Back to dashboard</Link>
    </div>
  );
}
