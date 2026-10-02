'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api/client';
import { Page, SupportQuery } from '@/lib/api/types';

export function useSupportQueries(params: { limit?: number; offset?: number } = {}) {
  const { limit = 20, offset = 0 } = params;
  const qs = new URLSearchParams({ limit: String(limit), offset: String(offset) });

  // Note: the backend has no server-side status filter on this endpoint --
  // any filtering by status has to happen client-side on the returned page.
  return useQuery({
    queryKey: ['supportQueries', limit, offset],
    queryFn: () => api.get<Page<SupportQuery>>(`/admin/queries?${qs.toString()}`),
    refetchInterval: 20_000,
  });
}

export function useReplyToQuery() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      message,
      attachmentUrl,
      attachmentType,
    }: {
      id: number;
      message?: string;
      attachmentUrl?: string;
      attachmentType?: 'image' | 'audio';
    }) => api.post<SupportQuery>(`/admin/queries/${id}/reply`, { message, attachmentUrl, attachmentType }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['supportQueries'] }),
  });
}

export function useUpdateQueryStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, status }: { id: number; status: 'Open' | 'Pending' | 'Resolved' }) =>
      api.patch<SupportQuery>(`/admin/queries/${id}/status`, { status }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['supportQueries'] }),
  });
}

export function useDeleteQuery() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.delete<void>(`/admin/queries/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['supportQueries'] }),
  });
}
