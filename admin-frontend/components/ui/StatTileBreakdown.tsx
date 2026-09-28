import Link from 'next/link';
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

export interface StatBreakdownRow {
  label: string;
  value: string | number;
  href?: string;
  valueClassName?: string;
}

export default function StatTileBreakdown({
  label,
  value,
  icon,
  tone = 'brand',
  href,
  breakdown,
}: {
  label: string;
  value: string | number;
  icon?: IconKey;
  tone?: Tone;
  href?: string;
  breakdown: StatBreakdownRow[];
}) {
  const header = (
    <div className="flex items-start justify-between gap-2">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
      {icon && (
        <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${toneClasses[tone]}`}>
          <Icon name={icon} className="h-4 w-4" />
        </span>
      )}
    </div>
  );

  return (
    <div className="rounded-xl border border-slate-200/80 bg-white p-4 shadow-soft transition-all duration-200 hover:-translate-y-0.5 hover:shadow-card">
      {href ? (
        <Link href={href} className="block">
          {header}
          <p className="mt-2 text-2xl font-bold tracking-tight text-slate-900">{value}</p>
        </Link>
      ) : (
        <>
          {header}
          <p className="mt-2 text-2xl font-bold tracking-tight text-slate-900">{value}</p>
        </>
      )}
      <div className="mt-3 grid grid-cols-2 gap-x-3 gap-y-1.5 border-t border-slate-100 pt-2.5">
        {breakdown.map((row, i) =>
          row.href ? (
            <Link key={i} href={row.href} className="group flex items-baseline justify-between gap-1.5 rounded px-1 -mx-1 hover:bg-slate-50">
              <span className="text-[11px] text-slate-500 group-hover:text-brand-600">{row.label}</span>
              <span className={`text-xs font-semibold ${row.valueClassName ?? 'text-slate-700'} group-hover:text-brand-600`}>{row.value}</span>
            </Link>
          ) : (
            <div key={i} className="flex items-baseline justify-between gap-1.5 px-1">
              <span className="text-[11px] text-slate-500">{row.label}</span>
              <span className={`text-xs font-semibold ${row.valueClassName ?? 'text-slate-700'}`}>{row.value}</span>
            </div>
          )
        )}
      </div>
    </div>
  );
}
