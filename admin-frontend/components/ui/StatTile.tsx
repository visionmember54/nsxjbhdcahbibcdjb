import { Icon, type IconKey } from '@/components/layout/icons';

type Tone = 'brand' | 'blue' | 'amber' | 'purple' | 'slate' | 'emerald' | 'red';

const toneClasses: Record<Tone, string> = {
  brand: 'bg-brand-50 text-brand-600',
  blue: 'bg-blue-50 text-blue-600',
  amber: 'bg-amber-50 text-amber-600',
  purple: 'bg-purple-50 text-purple-600',
  slate: 'bg-slate-100 text-slate-500',
  emerald: 'bg-emerald-50 text-emerald-600',
  red: 'bg-red-50 text-red-600',
};

export default function StatTile({
  label,
  value,
  hint,
  icon,
  tone = 'brand',
  valueClassName = 'text-slate-900',
}: {
  label: string;
  value: string | number;
  hint?: string;
  icon?: IconKey;
  tone?: Tone;
  valueClassName?: string;
}) {
  return (
    <div className="group rounded-xl border border-slate-200/80 bg-white p-4 shadow-soft transition-all duration-200 hover:-translate-y-0.5 hover:shadow-card">
      <div className="flex items-start justify-between gap-2">
        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
        {icon && (
          <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${toneClasses[tone]}`}>
            <Icon name={icon} className="h-4 w-4" />
          </span>
        )}
      </div>
      <p className={`mt-2 text-2xl font-bold tracking-tight ${valueClassName}`}>{value}</p>
      {hint && <p className="mt-1 text-xs text-slate-400">{hint}</p>}
    </div>
  );
}
