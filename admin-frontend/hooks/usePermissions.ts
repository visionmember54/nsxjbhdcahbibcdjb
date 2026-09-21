'use client';

import { useCurrentAdmin } from './useAuth';

export function usePermissions() {
  const { data: me } = useCurrentAdmin();
  const permissions = new Set(me?.permissions ?? []);
  return {
    has: (code: string) => permissions.has(code),
    permissions,
  };
}
