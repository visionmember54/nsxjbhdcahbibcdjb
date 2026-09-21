'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api/client';
import { Page, Student, UserStats, UserPaymentInfo, UserWithdrawal, UserBid, UserTransaction, UserWinning } from '@/lib/api/types';

export function useStudents(params: { limit?: number; offset?: number; search?: string; status?: 'active' | 'disabled' } = {}) {
  const { limit = 20, offset = 0, search, status } = params;
  const qs = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (search?.trim()) qs.set('search', search.trim());
  if (status) qs.set('status', status);
  return useQuery({
    queryKey: ['students', limit, offset, search ?? '', status ?? ''],
    queryFn: () => api.get<Page<Student>>(`/admin/users?${qs.toString()}`),
  });
}

export function useCreateStudent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: { name: string; phone: string; email?: string; password?: string }) =>
      api.post<Student & { temporary_password?: string | null }>('/admin/users', payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['students'] }),
  });
}

export function useUpdateStudent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, status, reason }: { id: number; status: 'active' | 'disabled'; reason?: string }) => api.patch<Student>(`/admin/users/${id}`, { status, reason }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['students'] }),
  });
}

export function useStudent(studentId: number | null) {
  return useQuery({
    queryKey: ['student', studentId],
    queryFn: () => api.get<Student>(`/admin/users/${studentId}`),
    enabled: studentId != null,
  });
}

/** id -> student lookup, for anywhere a list shows a raw user_id and needs
 * to render a name (simulations, credit ledger, ...). Mirrors useMarketsLookup. */
export function useStudentsLookup() {
  const query = useQuery({
    queryKey: ['studentsLookup'],
    queryFn: () => api.get<Page<Student>>('/admin/users?limit=200'),
  });

  const byId = new Map<number, Student>();
  query.data?.items.forEach((s) => byId.set(s.id, s));

  return { ...query, byId };
}

export function useUserStats(studentId: number | null) {
  return useQuery({
    queryKey: ['studentStats', studentId],
    queryFn: () => api.get<UserStats>(`/admin/users/${studentId}/stats`),
    enabled: studentId != null,
  });
}

export function useUserPaymentInfo(studentId: number | null) {
  return useQuery({
    queryKey: ['studentPaymentInfo', studentId],
    queryFn: () => api.get<UserPaymentInfo[]>(`/admin/users/${studentId}/payment-info`),
    enabled: studentId != null,
  });
}

export function useUserWithdrawals(studentId: number | null) {
  return useQuery({
    queryKey: ['studentWithdrawals', studentId],
    queryFn: () => api.get<UserWithdrawal[]>(`/admin/users/${studentId}/withdrawals`),
    enabled: studentId != null,
  });
}

export function useUserBids(studentId: number | null) {
  return useQuery({
    queryKey: ['studentBids', studentId],
    queryFn: () => api.get<UserBid[]>(`/admin/users/${studentId}/bids`),
    enabled: studentId != null,
  });
}

export function useUserTransactions(studentId: number | null) {
  return useQuery({
    queryKey: ['studentTransactions', studentId],
    queryFn: () => api.get<UserTransaction[]>(`/admin/users/${studentId}/transactions`),
    enabled: studentId != null,
  });
}

export function useUserWinnings(studentId: number | null) {
  return useQuery({
    queryKey: ['studentWinnings', studentId],
    queryFn: () => api.get<UserWinning[]>(`/admin/users/${studentId}/winnings`),
    enabled: studentId != null,
  });
}

export function useResetPassword() {
  return useMutation({
    mutationFn: (studentId: number) => api.post<{ message: string; temporary_password: string }>(`/admin/users/${studentId}/reset-password`),
  });
}
