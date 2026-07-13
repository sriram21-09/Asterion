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
          set({
            measurements: response.measurements,
            scenarioId: response.scenario_id,
            towerCount: response.tower_count,
            measurementCount: response.measurement_count,
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
