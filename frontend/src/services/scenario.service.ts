import { api } from '@/lib/api';
import type { Scenario, CreateScenarioDTO, UpdateScenarioDTO } from '@/types/scenario';

export const scenarioService = {
  getScenarios: async (): Promise<Scenario[]> => {
    const { data } = await api.get<Scenario[]>('/scenarios');
    return data;
  },

  getScenario: async (id: string): Promise<Scenario> => {
    const { data } = await api.get<Scenario>(`/scenarios/${id}`);
    return data;
  },

  createScenario: async (payload: CreateScenarioDTO): Promise<Scenario> => {
    const { data } = await api.post<Scenario>('/scenarios', payload);
    return data;
  },
  
  updateScenario: async (id: string, payload: UpdateScenarioDTO): Promise<Scenario> => {
    const { data } = await api.put<Scenario>(`/scenarios/${id}`, payload);
    return data;
  },

  deleteScenario: async (id: string): Promise<void> => {
    await api.delete(`/scenarios/${id}`);
  },
};
