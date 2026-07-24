import { api } from '@/lib/api';
import type {
  LocalizationRequest,
  LocalizationResponse,
} from '@/types/scientific';



/**
 * Service layer for the localization API endpoint (`/api/v1/localization/run`).
 */
export const localizationService = {
  /**
   * Run the localization engine against a set of tower signals.
   *
   * POST /api/v1/localization/run
   */
  runLocalization: async (
    payload: LocalizationRequest,
  ): Promise<LocalizationResponse> => {
    const { data } = await api.post<LocalizationResponse>(
      '/localization/run',
      payload,
    );
    return data;
  },
};
