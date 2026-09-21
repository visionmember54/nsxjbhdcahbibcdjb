type Tone = 'green' | 'amber' | 'red' | 'slate' | 'blue' | 'purple';

const toneClasses: Record<Tone, string> = {
  green: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  amber: 'bg-amber-50 text-amber-700 ring-amber-600/20',
  red: 'bg-red-50 text-red-700 ring-red-600/20',
  slate: 'bg-slate-100 text-slate-600 ring-slate-500/20',
  blue: 'bg-blue-50 text-blue-700 ring-blue-600/20',
  purple: 'bg-purple-50 text-purple-700 ring-purple-600/20',
};

const dotClasses: Record<Tone, string> = {
  green: 'bg-emerald-500',
  amber: 'bg-amber-500',
  red: 'bg-red-500',
  slate: 'bg-slate-400',
  blue: 'bg-blue-500',
  purple: 'bg-purple-500',
};

export default function Badge({ children, tone = 'slate' }: { children: React.ReactNode; tone?: Tone }) {
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${toneClasses[tone]}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${dotClasses[tone]}`} aria-hidden="true" />
      {children}
    </span>
  );
}

const STATUS_TONE: Record<string, Tone> = {
  active: 'green',
  Active: 'green',
  OPEN: 'green',
  Won: 'green',
  Published: 'green',
  disabled: 'slate',
  Inactive: 'slate',
  UPCOMING: 'blue',
  CLOSED: 'amber',
  RESULT_PENDING: 'amber',
  Pending: 'amber',
  Draft: 'amber',
  SUSPENDED: 'red',
  Lost: 'red',
  Cancelled: 'slate',
  Corrected: 'purple',
  RESULT_PUBLISHED: 'purple',
};

export function StatusBadge({ status }: { status: string }) {
  return <Badge tone={STATUS_TONE[status] ?? 'slate'}>{status}</Badge>;
}
