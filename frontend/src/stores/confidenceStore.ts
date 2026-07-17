import { create } from 'zustand';
import type { ConfidenceRunResponse } from '@/types/scientific';
import { confidenceService } from '@/services/confidenceService';

// ── Store Interface ─────────────────────────────────────────────────────

interface ConfidenceState {
  // ── Result ──────────────────────────────────────────────────────
  result: ConfidenceRunResponse | null;

  // ── Status ──────────────────────────────────────────────────────
  isRunning: boolean;
  error: string | null;

  // ── Actions ─────────────────────────────────────────────────────
  /**
   * Call the confidence analysis API for a given case and hydrate
   * the store with the result.
   */
  runConfidence: (caseCode: string) => Promise<void>;

  /** Clear all confidence results. */
  clearResults: () => void;
}

// ── Initial / reset slice ───────────────────────────────────────────────

const INITIAL_STATE = {
  result: null as ConfidenceRunResponse | null,
  isRunning: false,
  error: null as string | null,
} as const;

// ── Store ────────────────────────────────────────────────────────────────

export const useConfidenceStore = create<ConfidenceState>()((set) => ({
  ...INITIAL_STATE,

  runConfidence: async (caseCode) => {
    set({ isRunning: true, error: null });

    try {
      const response = await confidenceService.runConfidence(caseCode);

      set({
        result: response,
        isRunning: false,
        error: null,
      });
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : 'Confidence analysis failed';
      set({
        isRunning: false,
        error: message,
      });
      throw err;
    }
  },

  clearResults: () => set({ ...INITIAL_STATE }),
}));
