import { api } from '@/lib/api';

export interface DatabaseOperationResult {
  message: string;
  deleted?: Record<string, number>;
  scenarios_created?: number;
  cases_created?: number;
}

export const systemService = {
  resetDatabase: async (): Promise<DatabaseOperationResult> => {
    const { data } = await api.post<DatabaseOperationResult>('/system/database/reset');
    return data;
  },

  seedDatabase: async (): Promise<DatabaseOperationResult> => {
    const { data } = await api.post<DatabaseOperationResult>('/system/database/seed');
    return data;
  },
};
