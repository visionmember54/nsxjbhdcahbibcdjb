'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api/client';
import { MarketResult, Page, ResultPreview } from '@/lib/api/types';

export function useResults(
  params: { marketId?: number; status?: string; dateFrom?: string; dateTo?: string; limit?: number; offset?: number } = {}
) {
  const { marketId, status, dateFrom, dateTo, limit = 20, offset = 0 } = params;
  const qs = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (marketId != null) qs.set('market_id', String(marketId));
  if (status) qs.set('status_filter', status);
  if (dateFrom) qs.set('date_from', dateFrom);
  if (dateTo) qs.set('date_to', dateTo);

  return useQuery({
    queryKey: ['results', marketId ?? null, status ?? null, dateFrom ?? null, dateTo ?? null, limit, offset],
    queryFn: () => api.get<Page<MarketResult>>(`/admin/results?${qs.toString()}`),
  });
}

function invalidateResults(qc: ReturnType<typeof useQueryClient>) {
  qc.invalidateQueries({ queryKey: ['results'] });
  qc.invalidateQueries({ queryKey: ['simulations'] });
  qc.invalidateQueries({ queryKey: ['students'] });
  qc.invalidateQueries({ queryKey: ['dashboard'] });
  qc.invalidateQueries({ queryKey: ['markets'] });
}

export function useUpsertResult() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: {
      market_id: number;
      slot_id?: number | null;
      date: string;
      open_panna?: string | null;
      open_ank?: string | null;
      close_panna?: string | null;
      close_ank?: string | null;
      single_result?: string | null;
      publish: boolean;
    }) => api.post<MarketResult>('/admin/results', payload),
    onSuccess: () => invalidateResults(qc),
  });
}

export function usePreviewResult() {
  return useMutation({
    mutationFn: (payload: {
      market_id: number;
      slot_id?: number | null;
      open_panna?: string | null;
      open_ank?: string | null;
      close_panna?: string | null;
      close_ank?: string | null;
    }) => api.post<ResultPreview>('/admin/results/preview', payload),
  });
}

export function usePublishDraft() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (resultId: number) => api.post<MarketResult>(`/admin/results/${resultId}/publish`, {}),
    onSuccess: () => invalidateResults(qc),
  });
}

export function useCorrectResult() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      ...payload
    }: {
      id: number;
      reason: string;
      open_panna?: string | null;
      open_ank?: string | null;
      close_panna?: string | null;
      close_ank?: string | null;
      single_result?: string | null;
    }) => api.post<MarketResult>(`/admin/results/${id}/correct`, payload),
    onSuccess: () => invalidateResults(qc),
  });
}

export function useDeleteResult() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (resultId: number) => api.delete<void>(`/admin/results/${resultId}`),
    onSuccess: () => invalidateResults(qc),
  });
}
