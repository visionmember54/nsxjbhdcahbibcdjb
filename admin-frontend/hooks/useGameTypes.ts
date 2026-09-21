'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api/client';
import { GameType } from '@/lib/api/types';

export function useGameTypes() {
  return useQuery({
    queryKey: ['gameTypes'],
    queryFn: () => api.get<GameType[]>('/admin/game-types'),
  });
}

export function useCreateGameType() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: {
      code: string;
      name: string;
      description?: string;
      digit_length: number;
      classification_rule: string;
      display_order?: number;
    }) => api.post<GameType>('/admin/game-types', payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['gameTypes'] }),
  });
}

export function useUpdateGameType() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...payload }: { id: number; is_active?: boolean; display_order?: number }) =>
      api.patch<GameType>(`/admin/game-types/${id}`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['gameTypes'] }),
  });
}
