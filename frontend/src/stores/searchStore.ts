import { create } from 'zustand';
import { searchService } from '@/services/searchService';
import type { SearchResultItem } from '@/types/search';

interface SearchState {
  query: string;
  results: SearchResultItem[];
  total: number;
  isLoading: boolean;
  error: string | null;
  setQuery: (query: string) => void;
  executeSearch: (query: string) => Promise<void>;
  clearSearch: () => void;
}

export const useSearchStore = create<SearchState>((set) => ({
  query: '',
  results: [],
  total: 0,
  isLoading: false,
  error: null,

  setQuery: (query: string) => set({ query }),

  executeSearch: async (query: string) => {
    const trimmed = query.trim();
    if (!trimmed) {
      set({ results: [], total: 0, isLoading: false, error: null, query });
      return;
    }

    set({ isLoading: true, error: null, query });
    try {
      const response = await searchService.search(trimmed);
      set({
        results: response.results,
        total: response.total,
        isLoading: false,
      });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Search failed';
      set({
        isLoading: false,
        error: message,
      });
    }
  },

  clearSearch: () => set({ query: '', results: [], total: 0, isLoading: false, error: null }),
}));
