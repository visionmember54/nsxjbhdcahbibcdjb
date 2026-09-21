'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api/client';
import { Market, Page } from '@/lib/api/types';

/** A simple id -> market lookup, used anywhere a list shows market_id and
 * needs to render a name (results, simulations, reports). */
export function useMarketsLookup() {
  const query = useQuery({
    queryKey: ['marketsLookup'],
    queryFn: () => api.get<Page<Market>>('/admin/markets?limit=200'),
  });

  const byId = new Map<number, Market>();
  query.data?.items.forEach((m) => byId.set(m.id, m));

  return { ...query, byId, markets: query.data?.items ?? [] };
}
