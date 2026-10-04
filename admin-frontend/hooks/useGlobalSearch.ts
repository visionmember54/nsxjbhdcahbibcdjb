'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api/client';

export interface GlobalSearchResult {
  users: { id: number; name: string; phone: string; email: string }[];
  markets: { id: number; name: string; category: string }[];
  bid: { id: number; userId: number; userName: string | null; marketId: number; marketName: string | null; selection: string; status: string } | null;
}

export function useGlobalSearch(q: string) {
  const trimmed = q.trim();
  return useQuery({
    queryKey: ['globalSearch', trimmed],
    queryFn: () => api.get<GlobalSearchResult>(`/admin/search?q=${encodeURIComponent(trimmed)}`),
    enabled: trimmed.length > 0,
  });
}
