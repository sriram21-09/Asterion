import { api } from '@/lib/api';
import type {
  TrackingRequest,
  TrackingResponse,
} from '@/types/scientific';

/**
 * Service layer for the tracking API endpoint.
 *
 * Follows the same pattern as `simulationService.ts`:
 *   - Uses the shared `api` Axios instance (interceptors, base URL, etc.).
 *   - Each method returns unwrapped response data.
 */
export const trackingService = {
  /**
   * Run the Kalman-smoothed tracking pipeline for a given case.
   *
   * POST /tracking/run
   */
  runTracking: async (
    payload: TrackingRequest,
  ): Promise<TrackingResponse> => {
    const { data } = await api.post<TrackingResponse>(
      '/tracking/run',
      payload,
    );
    return data;
  },
};
