'use client';

import Link from 'next/link';
import { Td, Tr } from '@/components/ui/Table';
import Badge, { StatusBadge } from '@/components/ui/Badge';
import { useUpdateMarket } from '@/hooks/useMarkets';
import type { Market } from '@/lib/api/types';
import OrderInput from './OrderInput';

/** One market row -- its own useUpdateMarket instance so the order-save
 * spinner/checkmark is scoped to this row and never lights up every row
 * at once when only one is being edited. */
export default function MarketRow({ market, showCategory }: { market: Market; showCategory?: boolean }) {
  const updateMarket = useUpdateMarket();

  return (
    <Tr>
      <Td>
        <OrderInput
          value={market.display_order}
          pending={updateMarket.isPending}
          onSave={(next) => updateMarket.mutate({ id: market.id, display_order: next })}
        />
      </Td>
      <Td className="font-medium text-slate-900">{market.name}</Td>
      {showCategory && <Td className="text-slate-500">{market.category}</Td>}
      <Td>
        <StatusBadge status={market.effective_status} />
        {market.effective_status !== market.status && (
          <span className="ml-1.5 text-[10px] text-slate-400" title="Admin-set status; will auto-correct on the next status change">
            (set: {market.status})
          </span>
        )}
      </Td>
      <Td>{market.opening_time ?? '—'}</Td>
      <Td>{market.closing_time ?? '—'}</Td>
      <Td>{market.result_time ?? '—'}</Td>
      <Td>{market.visible ? <Badge tone="green">Visible</Badge> : <Badge tone="slate">Hidden</Badge>}</Td>
      <Td>
        <Link href={`/dashboard/markets/${market.id}`} className="text-xs font-semibold text-brand-600 hover:underline">
          Manage →
        </Link>
      </Td>
    </Tr>
  );
}
