import { create } from 'zustand';
import type {
  TrackingResult,
  TrackingRequest,
  Algorithm,
} from '@/types/scientific';
import { trackingService } from '@/services/trackingService';

// ── Store Interface ─────────────────────────────────────────────────────

interface TrackingState {
  // ── Result ──────────────────────────────────────────────────────
  result: TrackingResult | null;

  // ── Status ──────────────────────────────────────────────────────
  isRunning: boolean;
  error: string | null;

  // ── Actions ─────────────────────────────────────────────────────
  /**
   * Call the tracking API for a given case, enrich with wall-clock
   * timing, and hydrate the store with the result.
   */
  runTracking: (
    caseCode: string,
    algorithm?: Algorithm,
    smoothingFactor?: number,
  ) => Promise<void>;

  /** Clear all tracking results. */
  clearResults: () => void;
}

// ── Initial / reset slice ───────────────────────────────────────────────

const INITIAL_STATE = {
  result: null as TrackingResult | null,
  isRunning: false,
  error: null as string | null,
} as const;

// ── Store ────────────────────────────────────────────────────────────────

export const useTrackingStore = create<TrackingState>()((set) => ({
  ...INITIAL_STATE,

  runTracking: async (caseCode, algorithm, smoothingFactor) => {
    set({ isRunning: true, error: null });

    const request: TrackingRequest = {
      case_code: caseCode,
      ...(algorithm ? { algorithm } : {}),
      ...(smoothingFactor != null ? { smoothing_factor: smoothingFactor } : {}),
    };

    const startTime = performance.now();

    try {
      const response = await trackingService.runTracking(request);
      const elapsed = Math.round(performance.now() - startTime);

      const enrichedResult: TrackingResult = {
        ...response,
        time_elapsed_ms: elapsed,
      };

      set({
        result: enrichedResult,
        isRunning: false,
        error: null,
      });
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : 'Tracking failed';
      set({
        isRunning: false,
        error: message,
      });
      throw err;
    }
  },

  clearResults: () => set({ ...INITIAL_STATE }),
}));
