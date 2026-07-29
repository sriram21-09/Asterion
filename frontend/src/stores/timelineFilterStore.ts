import { create } from 'zustand'

export type EventCategory = 'Import' | 'Normalization' | 'Calls' | 'SMS' | 'Movement' | 'Validation';

interface TimelineFilterState {
  selectedCategories: EventCategory[];
  toggleCategory: (category: EventCategory) => void;
  setCategories: (categories: EventCategory[]) => void;
  resetFilters: () => void;
}

export const ALL_CATEGORIES: EventCategory[] = ['Import', 'Normalization', 'Calls', 'SMS', 'Movement', 'Validation'];

export const useTimelineFilterStore = create<TimelineFilterState>((set) => ({
  selectedCategories: ALL_CATEGORIES,
  toggleCategory: (category) =>
    set((state) => ({
      selectedCategories: state.selectedCategories.includes(category)
        ? state.selectedCategories.filter((c) => c !== category)
        : [...state.selectedCategories, category],
    })),
  setCategories: (categories) => set({ selectedCategories: categories }),
  resetFilters: () => set({ selectedCategories: ALL_CATEGORIES }),
}));
