'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api/client';
import { Permission, Role } from '@/lib/api/types';

export function useRoles() {
  return useQuery({
    queryKey: ['roles'],
    queryFn: () => api.get<Role[]>('/admin/roles'),
  });
}

export function usePermissionCatalog() {
  return useQuery({
    queryKey: ['permissionCatalog'],
    queryFn: () => api.get<Permission[]>('/admin/permissions'),
  });
}

export function useCreateRole() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: { slug: string; name: string }) => api.post<Role>('/admin/roles', payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['roles'] }),
  });
}

export function useSetRolePermissions() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ roleId, permissionCodes }: { roleId: number; permissionCodes: string[] }) =>
      api.put<Role>(`/admin/roles/${roleId}/permissions`, { permission_codes: permissionCodes }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['roles'] }),
  });
}
