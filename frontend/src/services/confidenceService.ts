import { api } from '@/lib/api';
import type { ConfidenceRunResponse } from '@/types/scientific';

/**
 * Service layer for the confidence analysis API endpoint.
 *
 * Follows the same pattern as `trackingService.ts`:
 *   - Uses the shared `api` Axios instance (interceptors, base URL, etc.).
 *   - Each method returns unwrapped response data.
 */
export const confidenceService = {
  /**
   * Run confidence analysis for a given case.
   *
   * POST /confidence/run?case_code={caseCode}
   */
  runConfidence: async (
    caseCode: string,
  ): Promise<ConfidenceRunResponse> => {
    const { data } = await api.post<ConfidenceRunResponse>(
      '/confidence/run',
      null,
      { params: { case_code: caseCode } },
    );
    return data;
  },
};
