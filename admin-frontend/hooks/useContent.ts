'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api/client';
import { EducationalContent, FAQ, HomepageBanner, ScrollingMessage, SiteSetting } from '@/lib/api/types';

// --- Site settings ---
export function useSiteSettings() {
  return useQuery({ queryKey: ['siteSettings'], queryFn: () => api.get<SiteSetting[]>('/admin/content/settings') });
}

export function useUpdateSiteSetting() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ key, value }: { key: string; value: string }) => api.put<SiteSetting>(`/admin/content/settings/${key}`, { value }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['siteSettings'] }),
  });
}

// --- Homepage banners ---
export function useBanners() {
  return useQuery({ queryKey: ['banners'], queryFn: () => api.get<HomepageBanner[]>('/admin/content/banners') });
}

export function useCreateBanner() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: { image_url?: string; title?: string; link?: string; display_order?: number }) =>
      api.post<HomepageBanner>('/admin/content/banners', payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['banners'] }),
  });
}

export function useUpdateBanner() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...payload }: { id: number; [key: string]: unknown }) => api.patch<HomepageBanner>(`/admin/content/banners/${id}`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['banners'] }),
  });
}

export function useDeleteBanner() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.delete<void>(`/admin/content/banners/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['banners'] }),
  });
}

// --- Scrolling messages ---
export function useScrollingMessages() {
  return useQuery({ queryKey: ['scrollingMessages'], queryFn: () => api.get<ScrollingMessage[]>('/admin/content/scrolling-messages') });
}

export function useCreateScrollingMessage() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: { text: string; display_order?: number }) => api.post<ScrollingMessage>('/admin/content/scrolling-messages', payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['scrollingMessages'] }),
  });
}

export function useUpdateScrollingMessage() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...payload }: { id: number; [key: string]: unknown }) =>
      api.patch<ScrollingMessage>(`/admin/content/scrolling-messages/${id}`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['scrollingMessages'] }),
  });
}

export function useDeleteScrollingMessage() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.delete<void>(`/admin/content/scrolling-messages/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['scrollingMessages'] }),
  });
}

// --- Educational content ---
export function useEducationalContent() {
  return useQuery({ queryKey: ['educationalContent'], queryFn: () => api.get<EducationalContent[]>('/admin/content/educational') });
}

export function useCreateEducationalContent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: {
      game_type_id?: number | null;
      title: string;
      description?: string;
      how_it_works?: string;
      example?: string;
      probability_explanation?: string;
      rules?: string;
    }) => api.post<EducationalContent>('/admin/content/educational', payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['educationalContent'] }),
  });
}

export function useUpdateEducationalContent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...payload }: { id: number; [key: string]: unknown }) => api.patch<EducationalContent>(`/admin/content/educational/${id}`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['educationalContent'] }),
  });
}

export function useDeleteEducationalContent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.delete<void>(`/admin/content/educational/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['educationalContent'] }),
  });
}

// --- FAQ ---
export function useFaqs() {
  return useQuery({ queryKey: ['faqs'], queryFn: () => api.get<FAQ[]>('/admin/content/faqs') });
}

export function useCreateFaq() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: { question: string; answer: string; display_order?: number }) => api.post<FAQ>('/admin/content/faqs', payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['faqs'] }),
  });
}

export function useUpdateFaq() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...payload }: { id: number; [key: string]: unknown }) => api.patch<FAQ>(`/admin/content/faqs/${id}`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['faqs'] }),
  });
}

export function useDeleteFaq() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.delete<void>(`/admin/content/faqs/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['faqs'] }),
  });
}
