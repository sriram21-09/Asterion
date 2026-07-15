import axios from 'axios';
import type {
  LocalizationRequest,
  LocalizationResponse,
} from '@/types/scientific';

// ── Standalone client ───────────────────────────────────────────────────
// The localization endpoint lives at `/api/localize` (outside the `/api/v1`
// prefix used by the shared `api` instance), so we create a thin wrapper
// that targets the API root directly.

const API_ROOT = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1')
  .replace(/\/api\/v1\/?$/, '');

const localizeClient = axios.create({
  baseURL: API_ROOT,
  timeout: 30_000,           // localization may be compute-heavy
  headers: { 'Content-Type': 'application/json' },
});

// Unwrap the APIResponse envelope the same way the shared interceptor does.
localizeClient.interceptors.response.use((response) => {
  if (
    response.data &&
    typeof response.data === 'object' &&
    response.data.success === true &&
    'data' in response.data
  ) {
    response.data = response.data.data;
  }
  return response;
});

// ── Service ─────────────────────────────────────────────────────────────

/**
 * Service layer for the localization API endpoint.
 *
 * Follows the same pattern as `simulationService.ts`:
 *   - Each method returns unwrapped response data.
 */
export const localizationService = {
  /**
   * Run the localization engine against a set of tower signals.
   *
   * POST /api/localize
   */
  runLocalization: async (
    payload: LocalizationRequest,
  ): Promise<LocalizationResponse> => {
    const { data } = await localizeClient.post<LocalizationResponse>(
      '/api/localize',
      payload,
    );
    return data;
  },
};
