import { create } from 'zustand';
import type {
  LocalizationResult,
  LocalizationRequest,
  TowerSignal,
  Measurement,
} from '@/types/scientific';
import { localizationService } from '@/services/localizationService';

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

// ── Measurement → TowerSignal adapter ───────────────────────────────────

function toTowerSignals(measurements: Measurement[]): TowerSignal[] {
  return measurements.map((m) => ({
    tower_id: m.tower_id,
    latitude: m.latitude ?? 0,
    longitude: m.longitude ?? 0,
    signal_strength_dbm: m.rssi_dbm,
    timestamp: new Date(m.timestamp).getTime() / 1000,
  }));
}

// ── Store ────────────────────────────────────────────────────────────────

export const useLocalizationStore = create<LocalizationState>()((set) => ({
  ...INITIAL_STATE,

  runLocalization: async (measurements, algorithm, expectedLat, expectedLon) => {
    set({ isRunning: true, error: null });

    const signals = toTowerSignals(measurements);
    const request: LocalizationRequest = {
      signals,
      ...(algorithm ? { algorithm: algorithm as LocalizationRequest['algorithm'] } : {}),
    };

    const startTime = performance.now();

    try {
      const response = await localizationService.runLocalization(request);
      const elapsed = Math.round(performance.now() - startTime);

      // Compute error distance if expected coordinates are known
      let errorDistance: number | null = null;
      if (expectedLat != null && expectedLon != null) {
        errorDistance = haversineMetres(
          expectedLat,
          expectedLon,
          response.estimated_latitude,
          response.estimated_longitude,
        );
      }

      const enrichedResult: LocalizationResult = {
        ...response,
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
