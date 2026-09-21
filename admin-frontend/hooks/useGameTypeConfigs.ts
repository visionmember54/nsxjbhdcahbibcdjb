'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api/client';
import { GameTypeConfig, Market, Page } from '@/lib/api/types';

export interface GameTypeConfigWithMarket extends GameTypeConfig {
  marketName: string;
  marketCategory: string;
}

/** Fans out across every market to build a per-game-type view (spec's
 * "Game Configuration" sidebar section), since config rows are stored
 * scoped to a market on the backend. */
export function useGameTypeConfigsByCode(code: string) {
  return useQuery({
    queryKey: ['gameTypeConfigsByCode', code],
    queryFn: async () => {
      const marketsPage = await api.get<Page<Market>>('/admin/markets?limit=100');
      const perMarket = await Promise.all(
        marketsPage.items.map(async (market) => {
          const configs = await api.get<GameTypeConfig[]>(`/admin/markets/${market.id}/game-type-configs`);
          return configs
            .filter((c) => c.game_type_code === code)
            .map((c): GameTypeConfigWithMarket => ({ ...c, marketName: market.name, marketCategory: market.category }));
        })
      );
      return perMarket.flat();
    },
  });
}

/** All configs across all markets, for the Bulk Mode overview. */
export function useAllGameTypeConfigs() {
  return useQuery({
    queryKey: ['gameTypeConfigsByCode', 'ALL'],
    queryFn: async () => {
      const marketsPage = await api.get<Page<Market>>('/admin/markets?limit=100');
      const perMarket = await Promise.all(
        marketsPage.items.map(async (market) => {
          const configs = await api.get<GameTypeConfig[]>(`/admin/markets/${market.id}/game-type-configs`);
          return configs.map((c): GameTypeConfigWithMarket => ({ ...c, marketName: market.name, marketCategory: market.category }));
        })
      );
      return perMarket.flat();
    },
  });
}

export function useGameTypeConfigs(marketId: number | null, slotId?: number | null) {
  const qs = new URLSearchParams();
  if (slotId != null) qs.set('slot_id', String(slotId));

  return useQuery({
    queryKey: ['gameTypeConfigs', marketId, slotId ?? null],
    queryFn: () => api.get<GameTypeConfig[]>(`/admin/markets/${marketId}/game-type-configs?${qs.toString()}`),
    enabled: marketId != null,
  });
}

export interface CreateGameTypeConfigPayload {
  game_type_id: number;
  slot_id?: number | null;
  stage?: string | null;
  enabled?: boolean;
  min_credits?: number;
  max_credits?: number;
  bulk_enabled?: boolean;
  max_bulk_selections?: number;
  same_amount_allowed?: boolean;
  individual_amount_allowed?: boolean;
  duplicate_selection_allowed?: boolean;
}

export function useCreateGameTypeConfig(marketId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateGameTypeConfigPayload) =>
      api.post<GameTypeConfig>(`/admin/markets/${marketId}/game-type-configs`, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['gameTypeConfigs', marketId] });
      qc.invalidateQueries({ queryKey: ['gameTypeConfigsByCode'] });
    },
  });
}

export function useUpdateGameTypeConfig(marketId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...payload }: { id: number } & Omit<CreateGameTypeConfigPayload, 'game_type_id'>) =>
      api.patch<GameTypeConfig>(`/admin/markets/${marketId}/game-type-configs/${id}`, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['gameTypeConfigs', marketId] });
      qc.invalidateQueries({ queryKey: ['gameTypeConfigsByCode'] });
    },
  });
}

/** Same PATCH, but for cross-market views (e.g. the per-game-type Game
 * Configuration pages) where marketId varies per row instead of being fixed
 * at hook-call time. */
export function useUpdateGameTypeConfigCrossMarket() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      marketId,
      id,
      ...payload
    }: { marketId: number; id: number } & Omit<CreateGameTypeConfigPayload, 'game_type_id'>) =>
      api.patch<GameTypeConfig>(`/admin/markets/${marketId}/game-type-configs/${id}`, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['gameTypeConfigs'] });
      qc.invalidateQueries({ queryKey: ['gameTypeConfigsByCode'] });
    },
  });
}
