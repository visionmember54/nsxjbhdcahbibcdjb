'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api/client';
import { MarketCategory } from '@/lib/api/types';

export function useMarketCategories() {
  return useQuery({
    queryKey: ['marketCategories'],
    queryFn: () => api.get<MarketCategory[]>('/admin/market-categories'),
  });
}

export function useCreateMarketCategory() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: { slug: string; name: string; display_order?: number }) =>
      api.post<MarketCategory>('/admin/market-categories', payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['marketCategories'] }),
  });
}
