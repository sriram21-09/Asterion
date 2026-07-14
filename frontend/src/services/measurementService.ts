import { api } from '@/lib/api';
import type { Measurement } from '@/types/scientific';

// ── Validation Request / Response DTOs ──────────────────────────────────

/**
 * A single structured validation error returned by the backend.
 */
export interface ValidationError {
  /** The field or measurement property that failed validation. */
  field: string;
  /** Human-readable description of the violation. */
  message: string;
  /** Severity level — `error` means the measurement was rejected. */
  severity: 'error' | 'warning';
  /** Index of the measurement in the submitted array (0-based). */
  measurement_index: number;
}

/**
 * Payload sent to `POST /measurements/validate`.
 */
export interface ValidateMeasurementsRequest {
  measurements: Measurement[];
}

/**
 * Response from `POST /measurements/validate`.
 */
export interface ValidateMeasurementsResponse {
  /** Overall pass/fail status for the batch. */
  is_valid: boolean;
  /** Number of measurements that passed all checks. */
  valid_count: number;
  /** Number of measurements rejected (at least one error-level issue). */
  rejected_count: number;
  /** Total warnings across all measurements. */
  warning_count: number;
  /** Flat list of structured errors & warnings. */
  errors: ValidationError[];
}

// ── Service ─────────────────────────────────────────────────────────────

/**
 * Service layer for measurement-related API endpoints.
 *
 * Follows the same pattern as `simulationService.ts`:
 *   - Uses the shared `api` Axios instance (interceptors, base URL, etc.).
 *   - Each method returns unwrapped response data.
 */
export const measurementService = {
  /**
   * Validate a batch of measurements against business rules
   * (coordinate bounds, RSSI range, timestamp plausibility, etc.).
   *
   * POST /measurements/validate
   */
  validateMeasurements: async (
    payload: ValidateMeasurementsRequest,
  ): Promise<ValidateMeasurementsResponse> => {
    const { data } = await api.post<ValidateMeasurementsResponse>(
      '/measurements/validate',
      payload,
    );
    return data;
  },
};
