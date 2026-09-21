'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api/client';
import { Market, Page } from '@/lib/api/types';

export function useMarkets(params: { category?: string; limit?: number; offset?: number } = {}) {
  const { category, limit = 50, offset = 0 } = params;
  const qs = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (category) qs.set('category', category);

  return useQuery({
    queryKey: ['markets', category ?? 'all', limit, offset],
    queryFn: () => api.get<Page<Market>>(`/admin/markets?${qs.toString()}`),
  });
}

export function useMarket(marketId: number | null) {
  return useQuery({
    queryKey: ['market', marketId],
    queryFn: () => api.get<Market>(`/markets/${marketId}`),
    enabled: marketId != null,
  });
}

export function useCreateMarket() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: {
      category_id: number;
      name: string;
      slug: string;
      description?: string;
      opening_time?: string | null;
      closing_time?: string | null;
      result_time?: string | null;
      display_order?: number;
    }) => api.post<Market>('/admin/markets', payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['markets'] }),
  });
}

export function useUpdateMarket() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...payload }: { id: number; [key: string]: unknown }) => api.patch<Market>(`/admin/markets/${id}`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['markets'] }),
  });
}

export function useUpdateMarketStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) => api.post<Market>(`/admin/markets/${id}/status`, { status }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['markets'] });
      qc.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
}
