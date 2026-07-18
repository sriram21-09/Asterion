import { create } from 'zustand';
import type { EvidenceResponse } from '@/types/scientific';
import { evidenceService } from '@/services/evidenceService';

// ── Store Interface ─────────────────────────────────────────────────────

interface EvidenceState {
  // ── Result ──────────────────────────────────────────────────────
  evidence: EvidenceResponse | null;

  // ── Status ──────────────────────────────────────────────────────
  isLoading: boolean;
  error: string | null;

  // ── Actions ─────────────────────────────────────────────────────
  /**
   * Fetch the evidence audit packet for a given case and hydrate
   * the store with the result.
   */
  fetchEvidence: (caseCode: string) => Promise<void>;

  /** Clear all evidence data. */
  clearEvidence: () => void;
}

// ── Initial / reset slice ───────────────────────────────────────────────

const INITIAL_STATE = {
  evidence: null as EvidenceResponse | null,
  isLoading: false,
  error: null as string | null,
} as const;

// ── Store ────────────────────────────────────────────────────────────────

export const useEvidenceStore = create<EvidenceState>()((set) => ({
  ...INITIAL_STATE,

  fetchEvidence: async (caseCode) => {
    set({ isLoading: true, error: null });

    try {
      const response = await evidenceService.getEvidence(caseCode);

      set({
        evidence: response,
        isLoading: false,
        error: null,
      });
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : 'Evidence retrieval failed';
      set({
        isLoading: false,
        error: message,
      });
      throw err;
    }
  },

  clearEvidence: () => set({ ...INITIAL_STATE }),
}));
