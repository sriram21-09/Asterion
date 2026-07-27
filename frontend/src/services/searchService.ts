import { api } from '@/lib/api';
import type { PaginatedSearchResponse } from '@/types/search';

export const searchService = {
  search: async (query: string, limit = 10, offset = 0): Promise<PaginatedSearchResponse> => {
    const trimmed = query.trim();
    if (!trimmed) {
      return {
        results: [],
        total: 0,
        limit,
        offset,
        query,
      };
    }
    const { data } = await api.get<PaginatedSearchResponse>('/search', {
      params: { q: trimmed, limit, offset },
    });
    return data;
  },
};
