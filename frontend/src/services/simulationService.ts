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
    // Derive case_code from scenario_id (e.g. 1 or SCN-CFG-001 -> CASE-001)
    const idNum = typeof payload.scenario_id === 'number'
      ? payload.scenario_id
      : parseInt(String(payload.scenario_id).replace(/\D/g, ''), 10) || 1;
    const caseCode = `CASE-${String(idNum).padStart(3, '0')}`;

    const { data } = await api.post<GenerateSimulationResponse>(
      `/simulation/generate?case_code=${caseCode}`,
      payload.simulation || {}
    );
    return data;
  },
};
