'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api/client';
import { GameStatistic, MarketStatistic, NumberFrequency } from '@/lib/api/types';

export function useMarketStatistics() {
  return useQuery({
    queryKey: ['reports', 'marketStatistics'],
    queryFn: () => api.get<MarketStatistic[]>('/admin/reports/simulation-statistics'),
  });
}

export function useGameStatistics() {
  return useQuery({
    queryKey: ['reports', 'gameStatistics'],
    queryFn: () => api.get<GameStatistic[]>('/admin/reports/game-statistics'),
  });
}

export function useNumberFrequency(params: { marketId?: number; gameType?: string; limit?: number } = {}) {
  const { marketId, gameType, limit = 20 } = params;
  const qs = new URLSearchParams({ limit: String(limit) });
  if (marketId != null) qs.set('market_id', String(marketId));
  if (gameType) qs.set('game_type', gameType);

  return useQuery({
    queryKey: ['reports', 'numberFrequency', marketId ?? null, gameType ?? null, limit],
    queryFn: () => api.get<NumberFrequency[]>(`/admin/reports/number-frequency?${qs.toString()}`),
  });
}
