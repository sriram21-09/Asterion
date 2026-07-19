import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type {
  SimulationParameters,
  PropagationDefaults,
  Measurement,
  GenerateSimulationRequest,
  EnvironmentType,
} from '@/types/scientific';
import { simulationService } from '@/services/simulationService';

// ── Default Values ──────────────────────────────────────────────────────

const DEFAULT_SIMULATION_PARAMS: Required<SimulationParameters> = {
  algorithm: 'multilateration',
  max_iterations: 100,
  convergence_threshold_m: 1.0,
  measurement_count: 1,
  enable_noise: true,
  random_seed: null as unknown as number,
};

const DEFAULT_PROPAGATION: Required<PropagationDefaults> = {
  path_loss_exponent: 3.5,
  shadow_fading_std_db: 8.0,
  reference_distance_m: 1.0,
  reference_loss_db: 38.0,
};

// ── Store Interface ─────────────────────────────────────────────────────

interface SimulationState {
  // ── Parameters ──────────────────────────────────────────────────
  simulationParams: SimulationParameters;
  propagationDefaults: PropagationDefaults;
  environmentType: EnvironmentType;

  // ── Generated Results ───────────────────────────────────────────
  measurements: Measurement[];
  scenarioId: string | null;
  towerCount: number;
  measurementCount: number;

  // ── Status ──────────────────────────────────────────────────────
  isGenerating: boolean;
  error: string | null;

  // ── Actions ─────────────────────────────────────────────────────
  setSimulationParams: (params: Partial<SimulationParameters>) => void;
  setPropagationDefaults: (defaults: Partial<PropagationDefaults>) => void;
  setEnvironmentType: (env: EnvironmentType) => void;
  generateMeasurements: (request: GenerateSimulationRequest) => Promise<void>;
  fetchMeasurements: (caseCode: string) => Promise<void>;
  clearResults: () => void;
  resetParams: () => void;
}

// ── Store ────────────────────────────────────────────────────────────────

export const useSimulationStore = create<SimulationState>()(
  persist(
    (set) => ({
      // ── Initial State ─────────────────────────────────────────────
      simulationParams: { ...DEFAULT_SIMULATION_PARAMS },
      propagationDefaults: { ...DEFAULT_PROPAGATION },
      environmentType: 'urban',

      measurements: [],
      scenarioId: null,
      towerCount: 0,
      measurementCount: 0,

      isGenerating: false,
      error: null,

      // ── Parameter Actions ─────────────────────────────────────────

      setSimulationParams: (params) =>
        set((state) => ({
          simulationParams: { ...state.simulationParams, ...params },
        })),

      setPropagationDefaults: (defaults) =>
        set((state) => ({
          propagationDefaults: { ...state.propagationDefaults, ...defaults },
        })),

      setEnvironmentType: (env) => set({ environmentType: env }),

      // ── Generation Action ─────────────────────────────────────────

      generateMeasurements: async (request) => {
        set({ isGenerating: true, error: null });
        try {
          const response = await simulationService.generateMeasurements(request);
          
          const rawList = Array.isArray(response) ? response : (response as any).measurements || [];
          const measurementsList = rawList.map((m: any, idx: number) => {
            // Map measurement_code to measurement_id
            // Extract tower_id if present (e.g. MEAS-SCNXXX-TYYY-ZZZZ), otherwise fallback to round-robin
            const parts = (m.measurement_code || '').split('-');
            let towerId = null;
            for (const part of parts) {
              if (part.startsWith('T') && /^\d+$/.test(part.slice(1))) {
                towerId = part;
                break;
              }
            }
            if (!towerId) {
              const match = (m.measurement_code || '').match(/\d+/);
              const num = match ? parseInt(match[0], 10) : (idx + 1);
              const towerIndex = ((num - 1) % 3) + 1;
              towerId = `T${String(towerIndex).padStart(3, '0')}`;
            }

            return {
              measurement_id: m.measurement_code,
              tower_id: towerId,
              timestamp: m.timestamp,
              rssi_dbm: m.rssi_dbm,
              latitude: m.latitude,
              longitude: m.longitude,
              timing_advance: m.timing_advance,
              uncertainty_m: m.uncertainty_m,
            };
          });

          const scenarioId = Array.isArray(response) ? (response[0]?.scenario_code || null) : (response as any).scenario_id || null;
          const measurementCount = measurementsList.length;
          const towerCount = new Set(measurementsList.map((m: any) => m.tower_id)).size;

          set({
            measurements: measurementsList,
            scenarioId,
            towerCount,
            measurementCount,
            isGenerating: false,
            error: null,
          });
        } catch (err: unknown) {
          const message =
            err instanceof Error
              ? err.message
              : 'Failed to generate measurements';
          set({
            isGenerating: false,
            error: message,
          });
          throw err;
        }
      },

      fetchMeasurements: async (caseCode) => {
        set({ isGenerating: true, error: null });
        try {
          const response = await simulationService.getMeasurements(caseCode);
          
          const rawList = Array.isArray(response) ? response : (response as any).measurements || [];
          const measurementsList = rawList.map((m: any, idx: number) => {
            const parts = (m.measurement_code || '').split('-');
            let towerId = null;
            for (const part of parts) {
              if (part.startsWith('T') && /^\d+$/.test(part.slice(1))) {
                towerId = part;
                break;
              }
            }
            if (!towerId) {
              const match = (m.measurement_code || '').match(/\d+/);
              const num = match ? parseInt(match[0], 10) : (idx + 1);
              const towerIndex = ((num - 1) % 3) + 1;
              towerId = `T${String(towerIndex).padStart(3, '0')}`;
            }

            return {
              measurement_id: m.measurement_code,
              tower_id: towerId,
              timestamp: m.timestamp,
              rssi_dbm: m.rssi_dbm,
              latitude: m.latitude,
              longitude: m.longitude,
              timing_advance: m.timing_advance,
              uncertainty_m: m.uncertainty_m,
            };
          });

          const scenarioId = Array.isArray(response) ? (response[0]?.scenario_code || null) : (response as any).scenario_id || null;
          const measurementCount = measurementsList.length;
          const towerCount = new Set(measurementsList.map((m: any) => m.tower_id)).size;

          set({
            measurements: measurementsList,
            scenarioId,
            towerCount,
            measurementCount,
            isGenerating: false,
            error: null,
          });
        } catch (err: unknown) {
          const message =
            err instanceof Error ? err.message : 'Failed to fetch measurements';
          set({
            isGenerating: false,
            error: message,
          });
          throw err;
        }
      },

      // ── Reset Actions ─────────────────────────────────────────────

      clearResults: () =>
        set({
          measurements: [],
          scenarioId: null,
          towerCount: 0,
          measurementCount: 0,
          error: null,
        }),

      resetParams: () =>
        set({
          simulationParams: { ...DEFAULT_SIMULATION_PARAMS },
          propagationDefaults: { ...DEFAULT_PROPAGATION },
          environmentType: 'urban',
        }),
    }),
    {
      name: 'asterion-simulation',
      // Only persist parameters, not transient results / loading state
      partialize: (state) => ({
        simulationParams: state.simulationParams,
        propagationDefaults: state.propagationDefaults,
        environmentType: state.environmentType,
      }),
    },
  ),
);
