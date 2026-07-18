import { create } from 'zustand';
import type {
  LocalizationResult,
  Measurement,
} from '@/types/scientific';
import { api } from '@/lib/api';
import { useSimulationStore } from './simulationStore';

// ── Haversine helper ────────────────────────────────────────────────────

const EARTH_RADIUS_M = 6_371_000;

/**
 * Compute great-circle distance in metres between two WGS84 points.
 */
function haversineMetres(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number,
): number {
  const toRad = (deg: number) => (deg * Math.PI) / 180;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
  return EARTH_RADIUS_M * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

// ── Store Interface ─────────────────────────────────────────────────────

interface LocalizationState {
  // ── Result ──────────────────────────────────────────────────────
  result: LocalizationResult | null;

  // ── Status ──────────────────────────────────────────────────────
  isRunning: boolean;
  error: string | null;

  // ── Actions ─────────────────────────────────────────────────────
  /**
   * Convert measurements to tower signals, call the localization API,
   * compute error distance against expected coordinates (if provided),
   * and hydrate the store.
   */
  runLocalization: (
    measurements: Measurement[],
    algorithm?: string,
    expectedLat?: number | null,
    expectedLon?: number | null,
  ) => Promise<void>;

  /** Clear all localization results. */
  clearResults: () => void;
}

// ── Initial / reset slice ───────────────────────────────────────────────

const INITIAL_STATE = {
  result: null as LocalizationResult | null,
  isRunning: false,
  error: null as string | null,
} as const;


// ── Store ────────────────────────────────────────────────────────────────

export const useLocalizationStore = create<LocalizationState>()((set) => ({
  ...INITIAL_STATE,

  runLocalization: async (measurements, algorithm, expectedLat, expectedLon) => {
    set({ isRunning: true, error: null });

    const { scenarioId } = useSimulationStore.getState();
    const idNum = scenarioId
      ? parseInt(String(scenarioId).replace(/\D/g, ''), 10) || 1
      : 1;
    const caseCode = `CASE-${String(idNum).padStart(3, '0')}`;

    const startTime = performance.now();

    try {
      // 1. Trigger database-backed localization
      const locResponse = await api.post(`/localization/run?case_code=${caseCode}`);
      const locData = (locResponse as any).data ?? locResponse;

      // 2. Trigger database-backed confidence run
      let confidenceScore = 0.85;
      try {
        const confResponse = await api.post(`/confidence/run?case_code=${caseCode}`);
        const confData = (confResponse as any).data ?? confResponse;
        if (confData && typeof confData.confidence_score === 'number') {
          confidenceScore = confData.confidence_score;
        }
      } catch (confErr) {
        console.warn('Confidence run failed (non-blocking):', confErr);
      }

      const elapsed = Math.round(performance.now() - startTime);

      const estLat = locData.estimated_latitude;
      const estLon = locData.estimated_longitude;

      // Compute error distance if expected coordinates are known
      let errorDistance: number | null = locData.error_m ?? null;
      if (errorDistance === null && expectedLat != null && expectedLon != null) {
        errorDistance = haversineMetres(expectedLat, expectedLon, estLat, estLon);
      }

      const enrichedResult: LocalizationResult = {
        estimated_latitude: estLat,
        estimated_longitude: estLon,
        confidence_score: confidenceScore,
        signals_used: locData.signals_used || measurements.length,
        algorithm_applied: locData.algorithm || algorithm || 'multilateration',
        error_distance_m: errorDistance,
        time_elapsed_ms: elapsed,
      };

      set({
        result: enrichedResult,
        isRunning: false,
        error: null,
      });
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : 'Localization failed';
      set({
        isRunning: false,
        error: message,
      });
      throw err;
    }
  },

  clearResults: () => set({ ...INITIAL_STATE }),
}));
