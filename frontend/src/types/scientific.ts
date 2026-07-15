/**
 * Frontend type definitions for the Asterion scientific simulation layer.
 *
 * These interfaces mirror the backend Pydantic models in:
 *   - scientific/models/scenario_config.py  (TowerPlacement, PropagationDefaults, SimulationParameters)
 *   - scientific/models/measurement.py      (Measurement)
 *
 * Field names use snake_case to match the backend JSON contract exactly.
 */

// ── Environment Type ────────────────────────────────────────────────────

export type EnvironmentType = 'urban' | 'suburban' | 'rural' | 'highway';

export type Algorithm =
  | 'multilateration'
  | 'kalman'
  | 'weighted_centroid'
  | 'hybrid';

// ── Tower Placement ─────────────────────────────────────────────────────

/**
 * Lightweight tower position for simulation input.
 * Maps to `scientific.models.scenario_config.TowerPlacement`.
 */
export interface TowerPlacement {
  tower_id: string;
  latitude: number;
  longitude: number;
  antenna_height_m?: number;       // default 30.0
  frequency_mhz?: number;          // default 1800.0
  transmit_power_dbm?: number;     // default 43.0
  coverage_radius_m?: number;      // default 1000.0
  sector?: string | null;
}

// ── Propagation Defaults ────────────────────────────────────────────────

/**
 * Environment-specific RF propagation parameters.
 * Maps to `scientific.models.scenario_config.PropagationDefaults`.
 */
export interface PropagationDefaults {
  path_loss_exponent?: number;     // default 3.5
  shadow_fading_std_db?: number;   // default 8.0
  reference_distance_m?: number;   // default 1.0
  reference_loss_db?: number;      // default 38.0
}

// ── Simulation Parameters ───────────────────────────────────────────────

/**
 * Solver / iteration settings for the simulation engine.
 * Maps to `scientific.models.scenario_config.SimulationParameters`.
 */
export interface SimulationParameters {
  algorithm?: Algorithm;                // default "multilateration"
  max_iterations?: number;              // default 100
  convergence_threshold_m?: number;     // default 1.0
  measurement_count?: number;           // default 1
  enable_noise?: boolean;               // default true
  random_seed?: number | null;
}

// ── Measurement ─────────────────────────────────────────────────────────

/**
 * A single signal measurement captured from a cell tower.
 * Maps to `scientific.models.measurement.Measurement`.
 */
export interface Measurement {
  measurement_id: string;
  tower_id: string;
  timestamp: string;               // ISO 8601
  rssi_dbm: number;                // -150.0 to 0.0
  latitude?: number | null;
  longitude?: number | null;
  timing_advance?: number | null;
  uncertainty_m?: number | null;
}

// ── Request / Response DTOs ─────────────────────────────────────────────

/**
 * Payload sent to `POST /simulation/generate`.
 * Mirrors `ScenarioConfig` from the backend.
 */
export interface GenerateSimulationRequest {
  scenario_id: string;
  name: string;
  description?: string | null;
  tower_placements: TowerPlacement[];
  environment_type?: EnvironmentType;
  noise_level_dbm?: number;
  propagation?: PropagationDefaults;
  simulation?: SimulationParameters;
  expected_device_lat?: number | null;
  expected_device_lon?: number | null;
}

/**
 * Response from `POST /simulation/generate`.
 * The backend returns an array of generated Measurement objects.
 */
export interface GenerateSimulationResponse {
  measurements: Measurement[];
  scenario_id: string;
  tower_count: number;
  measurement_count: number;
}

// ── Localization ────────────────────────────────────────────────────────

/**
 * A single tower signal sent to the localization engine.
 * Maps to `TowerSignal` in `backend/main.py`.
 */
export interface TowerSignal {
  tower_id: string;
  latitude: number;
  longitude: number;
  signal_strength_dbm: number;
  timestamp: number;               // epoch seconds
}

/**
 * Payload sent to `POST /api/localize`.
 * Maps to `LocalizationRequest` in `backend/main.py`.
 */
export interface LocalizationRequest {
  signals: TowerSignal[];
  algorithm?: Algorithm;            // default "multilateration"
}

/**
 * Raw response from `POST /api/localize`.
 * Maps to `LocalizationResponse` in `backend/main.py`.
 */
export interface LocalizationResponse {
  estimated_latitude: number;
  estimated_longitude: number;
  confidence_score: number;         // 0–1
  signals_used: number;
  algorithm_applied: string;
}

/**
 * Client-enriched localization result.
 *
 * Extends the raw backend response with computed fields:
 *   - `error_distance_m`  — Haversine distance to expected coords (if known)
 *   - `time_elapsed_ms`   — wall-clock execution time
 */
export interface LocalizationResult extends LocalizationResponse {
  error_distance_m: number | null;
  time_elapsed_ms: number;
}
