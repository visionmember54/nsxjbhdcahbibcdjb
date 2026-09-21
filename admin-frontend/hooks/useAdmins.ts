'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api/client';
import { AdminUser, Page } from '@/lib/api/types';

export function useAdmins(params: { limit?: number; offset?: number } = {}) {
  const { limit = 20, offset = 0 } = params;
  return useQuery({
    queryKey: ['admins', limit, offset],
    queryFn: () => api.get<Page<AdminUser>>(`/admin/admins?limit=${limit}&offset=${offset}`),
  });
}

export function useCreateAdmin() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: { name: string; email: string; password: string; role: string }) =>
      api.post<AdminUser>('/admin/admins', payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admins'] }),
  });
}

export function useUpdateAdmin() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...payload }: { id: number; status?: string; role?: string }) => api.patch<AdminUser>(`/admin/admins/${id}`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admins'] }),
  });
}
