import { api } from '@/lib/api';
import type { Case, CreateCaseDTO } from '@/types/case';

const mapCaseResponse = (raw: any): Case => {
  return {
    id: String(raw.id),
    referenceNumber: raw.reference_number || raw.referenceNumber || `CAS-${String(raw.id).padStart(3, '0')}`,
    title: raw.title,
    description: raw.description || undefined,
    status: raw.status,
    createdAt: raw.created_at || raw.createdAt,
    updatedAt: raw.updated_at || raw.updatedAt,
  };
};

export const caseService = {
  getCases: async (): Promise<Case[]> => {
    const { data } = await api.get<any[]>('/cases');
    return data.map(mapCaseResponse);
  },

  getCase: async (id: string): Promise<Case> => {
    const { data } = await api.get<any>(`/cases/${id}`);
    return mapCaseResponse(data);
  },

  createCase: async (payload: CreateCaseDTO): Promise<Case> => {
    const backendPayload = {
      title: payload.title,
      description: payload.description,
      status: payload.status,
    };
    const { data } = await api.post<any>('/cases', backendPayload);
    return mapCaseResponse(data);
  },

  deleteCase: async (id: string): Promise<void> => {
    await api.delete(`/cases/${id}`);
  },
};
