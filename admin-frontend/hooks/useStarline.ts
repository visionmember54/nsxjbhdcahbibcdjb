'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api/client';
import { StarlineSlot } from '@/lib/api/types';

export function useStarlineSlots(marketId?: number | null) {
  const qs = new URLSearchParams();
  if (marketId != null) qs.set('market_id', String(marketId));

  return useQuery({
    queryKey: ['starlineSlots', marketId ?? null],
    queryFn: () => api.get<StarlineSlot[]>(`/admin/starline/slots?${qs.toString()}`),
  });
}

export function useCreateStarlineSlot() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: { market_id: number; slot_name: string; start_time: string; cutoff_time: string; display_order?: number }) =>
      api.post<StarlineSlot>('/admin/starline/slots', payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['starlineSlots'] }),
  });
}

export function useUpdateStarlineSlot() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...payload }: { id: number; [key: string]: unknown }) => api.patch<StarlineSlot>(`/admin/starline/slots/${id}`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['starlineSlots'] }),
  });
}
