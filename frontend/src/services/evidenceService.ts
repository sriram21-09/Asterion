import { api } from '@/lib/api';
import type { EvidenceResponse } from '@/types/scientific';

/**
 * Service layer for the evidence audit API endpoint.
 *
 * Follows the same pattern as `trackingService.ts`:
 *   - Uses the shared `api` Axios instance (interceptors, base URL, etc.).
 *   - Each method returns unwrapped response data.
 */
export const evidenceService = {
  /**
   * Retrieve the evidence audit packet for a given case.
   *
   * GET /evidence/{caseCode}
   */
  getEvidence: async (
    caseCode: string,
  ): Promise<EvidenceResponse> => {
    const { data } = await api.get<EvidenceResponse>(
      `/evidence/${encodeURIComponent(caseCode)}`,
    );
    return data;
  },
};
