'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api/client';
import { CreditRequest, Page } from '@/lib/api/types';

export function useCreditRequests(params: { limit?: number; offset?: number } = {}) {
  const { limit = 50, offset = 0 } = params;
  const qs = new URLSearchParams({ limit: String(limit), offset: String(offset) });

  return useQuery({
    queryKey: ['creditRequests', limit, offset],
    queryFn: () => api.get<Page<CreditRequest>>(`/admin/credit-requests?${qs.toString()}`),
    refetchInterval: 20_000,
  });
}

function invalidate(qc: ReturnType<typeof useQueryClient>) {
  qc.invalidateQueries({ queryKey: ['creditRequests'] });
  qc.invalidateQueries({ queryKey: ['students'] });
  qc.invalidateQueries({ queryKey: ['studentsLookup'] });
  qc.invalidateQueries({ queryKey: ['dashboard'] });
}

export function useApproveCreditRequest() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, adminNote }: { id: number; adminNote?: string }) =>
      api.post<CreditRequest>(`/admin/credit-requests/${id}/approve`, { admin_note: adminNote || undefined }),
    onSuccess: () => invalidate(qc),
  });
}

export function useRejectCreditRequest() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, adminNote }: { id: number; adminNote?: string }) =>
      api.post<CreditRequest>(`/admin/credit-requests/${id}/reject`, { admin_note: adminNote || undefined }),
    onSuccess: () => invalidate(qc),
  });
}
