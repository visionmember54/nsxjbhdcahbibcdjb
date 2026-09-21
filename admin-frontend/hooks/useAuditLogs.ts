'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api/client';
import { AuditLogEntry, Page } from '@/lib/api/types';

export function useAuditLogs(params: { limit?: number; offset?: number; userId?: number } = {}) {
  const { limit = 20, offset = 0, userId } = params;
  const suffix = userId != null ? `&user_id=${userId}` : '';
  return useQuery({
    queryKey: ['auditLogs', limit, offset, userId ?? null],
    queryFn: () => api.get<Page<AuditLogEntry>>(`/admin/audit-logs?limit=${limit}&offset=${offset}${suffix}`),
  });
}
