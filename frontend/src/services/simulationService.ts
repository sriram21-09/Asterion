import { api } from '@/lib/api';
import type {
  GenerateSimulationRequest,
  GenerateSimulationResponse,
} from '@/types/scientific';

/**
 * Service layer for the simulation API endpoints.
 *
 * Follows the same pattern as `scenario.service.ts` and `case.service.ts`:
 *   - Uses the shared `api` Axios instance (interceptors, base URL, etc.).
 *   - Each method returns unwrapped response data.
 */
export const simulationService = {
  /**
   * Generate synthetic measurements for a given scenario configuration.
   *
   * POST /simulation/generate
   */
  generateMeasurements: async (
    payload: GenerateSimulationRequest,
  ): Promise<GenerateSimulationResponse> => {
    const { data } = await api.post<GenerateSimulationResponse>(
      '/simulation/generate',
      payload,
    );
    return data;
  },
};
