'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api/client';
import { Page } from '@/lib/api/types';

export interface GlobalCreditLedgerEntry {
  id: number;
  userId: number;
  userName: string;
  userPhone: string;
  type: string;
  amount: number;
  balanceAfter: number;
  referenceType: string | null;
  referenceId: string | null;
  note: string | null;
  createdAt: string;
}

export function useGlobalCreditLedger(params: { limit?: number; offset?: number; type?: string } = {}) {
  const { limit = 20, offset = 0, type } = params;
  const qs = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (type) qs.set('type_filter', type);

  return useQuery({
    queryKey: ['globalCreditLedger', limit, offset, type ?? null],
    queryFn: () => api.get<Page<GlobalCreditLedgerEntry>>(`/admin/credit-ledger?${qs.toString()}`),
    refetchInterval: 20_000,
  });
}
