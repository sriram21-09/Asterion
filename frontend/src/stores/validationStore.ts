import { create } from 'zustand';
import type {
  ValidateMeasurementsResponse,
  ValidationError,
} from '@/services/measurementService';
import { measurementService } from '@/services/measurementService';
import type { Measurement } from '@/types/scientific';

// ── Store Interface ─────────────────────────────────────────────────────

interface ValidationState {
  // ── Results ──────────────────────────────────────────────────────
  /** Whether the most-recent batch passed validation overall. */
  isValid: boolean | null;
  /** Number of measurements that passed all checks. */
  validCount: number;
  /** Number of measurements rejected due to error-level issues. */
  rejectedCount: number;
  /** Total warning count across the batch. */
  warningCount: number;
  /** Flat list of structured errors & warnings. */
  errors: ValidationError[];

  // ── Status ──────────────────────────────────────────────────────
  isValidating: boolean;
  validationError: string | null;

  // ── Actions ─────────────────────────────────────────────────────
  /** Fire the validation request and hydrate the store with results. */
  validateMeasurements: (measurements: Measurement[]) => Promise<void>;
  /** Clear all validation results (e.g. when the user regenerates data). */
  clearValidation: () => void;
}

// ── Initial / reset slice ───────────────────────────────────────────────

const INITIAL_STATE = {
  isValid: null,
  validCount: 0,
  rejectedCount: 0,
  warningCount: 0,
  errors: [] as ValidationError[],
  isValidating: false,
  validationError: null,
} as const;

// ── Store ────────────────────────────────────────────────────────────────

export const useValidationStore = create<ValidationState>()((set) => ({
  ...INITIAL_STATE,

  // ── Validate Action ────────────────────────────────────────────────

  validateMeasurements: async (measurements) => {
    set({ isValidating: true, validationError: null });
    try {
      const response: ValidateMeasurementsResponse =
        await measurementService.validateMeasurements({ measurements });

      set({
        isValid: response.is_valid,
        validCount: response.valid_count,
        rejectedCount: response.rejected_count,
        warningCount: response.warning_count,
        errors: response.errors,
        isValidating: false,
        validationError: null,
      });
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : 'Measurement validation failed';
      set({
        isValidating: false,
        validationError: message,
      });
      throw err;
    }
  },

  // ── Reset Action ───────────────────────────────────────────────────

  clearValidation: () => set({ ...INITIAL_STATE }),
}));
