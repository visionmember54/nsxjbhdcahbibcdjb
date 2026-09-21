'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api/client';
import { DashboardData } from '@/lib/api/types';

export function useDashboard() {
  return useQuery({
    queryKey: ['dashboard'],
    queryFn: () => api.get<DashboardData>('/admin/dashboard'),
  });
}
