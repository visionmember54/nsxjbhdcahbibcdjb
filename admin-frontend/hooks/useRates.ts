'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api/client';
import { Rate } from '@/lib/api/types';

export function useRates(marketId?: number | null) {
  const qs = new URLSearchParams();
  if (marketId != null) qs.set('market_id', String(marketId));

  return useQuery({
    queryKey: ['rates', marketId ?? null],
    queryFn: () => api.get<Rate[]>(`/admin/rates?${qs.toString()}`),
  });
}

export function useCreateRate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: { market_id: number; slot_id?: number | null; game_type_id: number; rate: number; effective_from: string }) =>
      api.post<Rate>('/admin/rates', payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['rates'] }),
  });
}

export function useUpdateRateStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, status }: { id: number; status: 'Active' | 'Inactive' }) => api.patch<Rate>(`/admin/rates/${id}`, { status }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['rates'] }),
  });
}
