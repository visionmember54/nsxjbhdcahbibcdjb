'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api/client';
import { Page, SimulationBatchResult, SimulationEntry } from '@/lib/api/types';

function invalidateAfterOverride(qc: ReturnType<typeof useQueryClient>) {
  qc.invalidateQueries({ queryKey: ['simulations'] });
  qc.invalidateQueries({ queryKey: ['students'] });
  qc.invalidateQueries({ queryKey: ['creditHistory'] });
  qc.invalidateQueries({ queryKey: ['dashboard'] });
}

export function useSimulations(params: { studentId?: number; marketId?: number; limit?: number; offset?: number } = {}) {
  const { studentId, marketId, limit = 20, offset = 0 } = params;
  const qs = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (studentId != null) qs.set('user_id', String(studentId));
  if (marketId != null) qs.set('market_id', String(marketId));

  return useQuery({
    queryKey: ['simulations', studentId ?? null, marketId ?? null, limit, offset],
    queryFn: () => api.get<Page<SimulationEntry>>(`/admin/simulations?${qs.toString()}`),
  });
}

export function useCreateSimulation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: {
      user_id: number;
      market_id: number;
      slot_id?: number | null;
      game_type: string;
      stage?: string | null;
      value: string;
      credits: number;
      game_variant?: 'OPEN_PANNA_CLOSE_ANK' | 'OPEN_ANK_CLOSE_PANNA';
    }) => api.post<SimulationBatchResult>('/admin/simulations', payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['simulations'] });
      qc.invalidateQueries({ queryKey: ['students'] });
      qc.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
}

export function useOverrideSimulation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, outcome, reason }: { id: number; outcome: 'Won' | 'Lost'; reason: string }) =>
      api.post<SimulationEntry>(`/admin/simulations/${id}/override`, { outcome, reason }),
    onSuccess: () => invalidateAfterOverride(qc),
  });
}

export function useCreateBulkSimulation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: {
      user_id: number;
      market_id: number;
      slot_id?: number | null;
      game_type: string;
      stage?: string | null;
      selections: { value: string; credits: number; game_variant?: 'OPEN_PANNA_CLOSE_ANK' | 'OPEN_ANK_CLOSE_PANNA' }[];
    }) => api.post<SimulationBatchResult>('/admin/simulations/bulk', payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['simulations'] });
      qc.invalidateQueries({ queryKey: ['students'] });
      qc.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
}
