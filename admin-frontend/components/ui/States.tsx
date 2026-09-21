export function LoadingState({ label = 'Loading…' }: { label?: string }) {
  return (
    <div role="status" aria-live="polite" className="flex items-center justify-center gap-2 py-16 text-sm font-medium text-slate-500">
      <svg className="h-4 w-4 animate-spin text-brand-500" viewBox="0 0 24 24" fill="none">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
      </svg>
      {label}
    </div>
  );
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div role="alert" className="flex flex-col items-center gap-2 py-12 text-center">
      <div className="rounded-full bg-red-50 p-3 text-red-600">
        <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
          <path
            fillRule="evenodd"
            d="M8.257 3.099c.765-1.36 2.72-1.36 3.486 0l6.28 11.18c.75 1.334-.213 2.98-1.742 2.98H3.72c-1.53 0-2.492-1.646-1.743-2.98l6.28-11.18zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-.25-6.5a.75.75 0 00-1.5 0v3.5a.75.75 0 001.5 0v-3.5z"
            clipRule="evenodd"
          />
        </svg>
      </div>
      <p className="text-sm font-medium text-slate-700">Something went wrong</p>
      <p className="max-w-sm text-xs text-slate-500">{message}</p>
    </div>
  );
}

export function EmptyState({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="flex flex-col items-center gap-2 py-12 text-center">
      <div className="rounded-full bg-slate-100 p-3 text-slate-400">
        <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
          <path d="M3 7.5a1.5 1.5 0 011.5-1.5h11a1.5 1.5 0 011.5 1.5v1.75a.75.75 0 01-.75.75H16a1 1 0 00-1 1 2 2 0 11-4 0 1 1 0 00-1-1H3.75a.75.75 0 01-.75-.75V7.5z" />
          <path d="M3 11.5h4.323a2.5 2.5 0 004.854 0H17v4a1.5 1.5 0 01-1.5 1.5h-11A1.5 1.5 0 013 15.5v-4z" />
        </svg>
      </div>
      <p className="text-sm font-medium text-slate-600">{title}</p>
      {hint && <p className="max-w-sm text-xs text-slate-400">{hint}</p>}
    </div>
  );
}
