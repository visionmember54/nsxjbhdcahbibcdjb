'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api/client';
import { CreditLedgerEntry, Page, Student } from '@/lib/api/types';

export function useCreditHistory(studentId: number | null, params: { limit?: number; offset?: number } = {}) {
  const { limit = 20, offset = 0 } = params;
  return useQuery({
    queryKey: ['creditHistory', studentId, limit, offset],
    queryFn: () => api.get<Page<CreditLedgerEntry>>(`/admin/users/${studentId}/credits/history?limit=${limit}&offset=${offset}`),
    enabled: studentId != null,
  });
}

function invalidateAfterCreditChange(qc: ReturnType<typeof useQueryClient>) {
  qc.invalidateQueries({ queryKey: ['students'] });
  qc.invalidateQueries({ queryKey: ['creditHistory'] });
  qc.invalidateQueries({ queryKey: ['dashboard'] });
}

export function useGrantCredits() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ studentId, amount, note, visibleToUser = true }: { studentId: number; amount: number; note: string; visibleToUser?: boolean }) =>
      api.post<Student>(`/admin/users/${studentId}/credits/grant`, { amount, note, visibleToUser }),
    onSuccess: () => invalidateAfterCreditChange(qc),
  });
}

export function useAdjustCredits() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ studentId, amount, note, visibleToUser = true }: { studentId: number; amount: number; note: string; visibleToUser?: boolean }) =>
      api.post<Student>(`/admin/users/${studentId}/credits/adjust`, { amount, note, visibleToUser }),
    onSuccess: () => invalidateAfterCreditChange(qc),
  });
}

export function useResetCredits() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ studentId, new_balance, note, visibleToUser = true }: { studentId: number; new_balance: number; note: string; visibleToUser?: boolean }) =>
      api.post<Student>(`/admin/users/${studentId}/credits/reset`, { new_balance, note, visibleToUser }),
    onSuccess: () => invalidateAfterCreditChange(qc),
  });
}
