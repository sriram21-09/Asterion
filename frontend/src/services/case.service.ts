import { api } from '@/lib/api';
import type { Case, CreateCaseDTO } from '@/types/case';

export const caseService = {
  getCases: async (): Promise<Case[]> => {
    const { data } = await api.get<Case[]>('/cases');
    return data;
  },

  getCase: async (id: number): Promise<Case> => {
    const { data } = await api.get<Case>(`/cases/${id}`);
    return data;
  },

  createCase: async (payload: CreateCaseDTO): Promise<Case> => {
    const { data } = await api.post<Case>('/cases', payload);
    return data;
  },

  deleteCase: async (id: number): Promise<void> => {
    await api.delete(`/cases/${id}`);
  },
};
