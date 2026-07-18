import { create } from 'zustand';
import { useSimulationStore } from './simulationStore';
import { useValidationStore } from './validationStore';
import { useLocalizationStore } from './localizationStore';
import { useTrackingStore } from './trackingStore';
import { useConfidenceStore } from './confidenceStore';
import { useEvidenceStore } from './evidenceStore';

// ── Pipeline Stage ──────────────────────────────────────────────────────

export type PipelineStage =
  | 'idle'
  | 'simulating'
  | 'validating'
  | 'localizing'
  | 'tracking'
  | 'confidence'
  | 'evidence'
  | 'complete'
  | 'failed';

// ── Pipeline Warning ────────────────────────────────────────────────────

export type WarningCategory =
  | 'validation_failure'
  | 'validation_warning'
  | 'algorithm_fallback'
  | 'low_confidence'
  | 'high_error_distance'
  | 'stage_error';

export type WarningSeverity = 'info' | 'warning' | 'danger';

export interface PipelineWarning {
  id: string;
  category: WarningCategory;
  severity: WarningSeverity;
  stage: PipelineStage;
  title: string;
  message: string;
  dismissed: boolean;
}

// ── Pipeline Stage Config ───────────────────────────────────────────────

const STAGE_LABELS: Record<string, string> = {
  simulating: 'Simulating',
  validating: 'Validating',
  localizing: 'Localizing',
  tracking: 'Tracking',
  confidence: 'Confidence',
  evidence: 'Evidence',
};

const STAGE_ICONS: Record<string, string> = {
  simulating: '⚡',
  validating: '🔍',
  localizing: '📍',
  tracking: '🛤️',
  confidence: '🛡️',
  evidence: '📋',
};

// ── Store Interface ─────────────────────────────────────────────────────

interface PipelineCoordinatorState {
  // ── State ──────────────────────────────────────────────────────
  currentStage: PipelineStage;
  warnings: PipelineWarning[];
  completedStages: PipelineStage[];
  pipelineError: string | null;
  lastRunTimestamp: string | null;
  isPipelineRunning: boolean;
  totalElapsedMs: number;

  // ── Actions ─────────────────────────────────────────────────────
  runFullPipeline: (scenarioId: number, scenarioName: string) => Promise<void>;
  clearPipeline: () => void;
  dismissWarning: (warningId: string) => void;
}

// ── Helpers ─────────────────────────────────────────────────────────────

let warningCounter = 0;

function createWarning(
  category: WarningCategory,
  severity: WarningSeverity,
  stage: PipelineStage,
  title: string,
  message: string,
): PipelineWarning {
  warningCounter += 1;
  return {
    id: `pw-${Date.now()}-${warningCounter}`,
    category,
    severity,
    stage,
    title,
    message,
    dismissed: false,
  };
}

function deriveCaseCode(scenarioId: number): string {
  return `CASE-${String(scenarioId).padStart(3, '0')}`;
}

// ── Initial State ───────────────────────────────────────────────────────

const INITIAL_STATE = {
  currentStage: 'idle' as PipelineStage,
  warnings: [] as PipelineWarning[],
  completedStages: [] as PipelineStage[],
  pipelineError: null as string | null,
  lastRunTimestamp: null as string | null,
  isPipelineRunning: false,
  totalElapsedMs: 0,
};

// ── Store ────────────────────────────────────────────────────────────────

export const usePipelineCoordinator = create<PipelineCoordinatorState>()(
  (set) => ({
    ...INITIAL_STATE,

    // ── Run Full Pipeline ─────────────────────────────────────────────
    runFullPipeline: async (scenarioId, scenarioName) => {
      const pipelineStart = performance.now();
      const caseCode = deriveCaseCode(scenarioId);
      const collectedWarnings: PipelineWarning[] = [];

      // Reset state
      set({
        currentStage: 'simulating',
        warnings: [],
        completedStages: [],
        pipelineError: null,
        isPipelineRunning: true,
        lastRunTimestamp: new Date().toISOString(),
        totalElapsedMs: 0,
      });

      // ── Console: Pipeline Start ────────────────────────────────────
      console.group(
        `%c🚀 ASTERION PIPELINE — Starting`,
        'color: #7c3aed; font-weight: bold; font-size: 14px',
      );
      console.log(`%cScenario: #${scenarioId} "${scenarioName}"`, 'color: #a78bfa');
      console.log(`%cCase Code: ${caseCode}`, 'color: #a78bfa');
      console.log(`%cTimestamp: ${new Date().toISOString()}`, 'color: #6b7280');
      console.log('─'.repeat(50));

      // ── Helper: advance stage ──────────────────────────────────────
      const advanceStage = (stage: PipelineStage) => {
        set((s) => ({
          currentStage: stage,
          completedStages: [...s.completedStages, s.currentStage],
        }));
      };

      const stageIndex = { current: 0 };
      const totalStages = 6;

      const logStageStart = (stage: string) => {
        stageIndex.current += 1;
        const icon = STAGE_ICONS[stage] || '▶';
        const label = STAGE_LABELS[stage] || stage;
        console.log(
          `%c[${stageIndex.current}/${totalStages}] ${icon} ${label}...`,
          'color: #60a5fa; font-weight: bold',
        );
      };

      const logStageSuccess = (detail: string) => {
        console.log(
          `%c   ✅ ${detail}`,
          'color: #34d399',
        );
      };

      const logStageWarning = (detail: string) => {
        console.log(
          `%c   ⚠️ ${detail}`,
          'color: #fbbf24',
        );
      };

      const logStageError = (detail: string) => {
        console.log(
          `%c   ❌ ${detail}`,
          'color: #f87171',
        );
      };

      try {
        // ════════════════════════════════════════════════════════════════
        // STAGE 1: Simulation — Generate Measurements
        // ════════════════════════════════════════════════════════════════
        logStageStart('simulating');

        const simulationStore = useSimulationStore.getState();
        await simulationStore.generateMeasurements({
          scenario_id: String(scenarioId),
          name: scenarioName,
          tower_placements: [],
          simulation: {
            algorithm: 'multilateration',
            max_iterations: 100,
            convergence_threshold_m: 1.0,
            measurement_count: 5,
            enable_noise: true,
          },
        });

        const { measurements } = useSimulationStore.getState();
        logStageSuccess(`${measurements.length} measurements generated`);

        if (measurements.length === 0) {
          throw new Error('Simulation produced zero measurements — cannot continue pipeline.');
        }

        // ════════════════════════════════════════════════════════════════
        // STAGE 2: Validation
        // ════════════════════════════════════════════════════════════════
        advanceStage('validating');
        logStageStart('validating');

        const validationStore = useValidationStore.getState();
        try {
          await validationStore.validateMeasurements(measurements);
          const valState = useValidationStore.getState();

          if (valState.isValid) {
            logStageSuccess(
              `All ${valState.validCount} measurement(s) passed`,
            );
          } else {
            logStageWarning(
              `${valState.rejectedCount} rejected, ${valState.warningCount} warning(s)`,
            );

            if (valState.rejectedCount > 0) {
              collectedWarnings.push(
                createWarning(
                  'validation_failure',
                  'warning',
                  'validating',
                  'Measurements Rejected',
                  `${valState.rejectedCount} of ${valState.validCount + valState.rejectedCount} measurement(s) were rejected during validation. The pipeline continues with accepted measurements.`,
                ),
              );
            }
            if (valState.warningCount > 0) {
              collectedWarnings.push(
                createWarning(
                  'validation_warning',
                  'info',
                  'validating',
                  'Validation Warnings',
                  `${valState.warningCount} non-blocking warning(s) were raised during validation. Review the Validation Summary for details.`,
                ),
              );
            }
          }
        } catch (valErr) {
          const msg = valErr instanceof Error ? valErr.message : 'Validation request failed';
          logStageError(`Validation failed: ${msg}`);
          collectedWarnings.push(
            createWarning(
              'stage_error',
              'warning',
              'validating',
              'Validation Unavailable',
              `Validation service returned an error: ${msg}. Pipeline continues without validation.`,
            ),
          );
        }

        // ════════════════════════════════════════════════════════════════
        // STAGE 3: Localization
        // ════════════════════════════════════════════════════════════════
        advanceStage('localizing');
        logStageStart('localizing');

        const localizationStore = useLocalizationStore.getState();
        try {
          await localizationStore.runLocalization(measurements);
          const locState = useLocalizationStore.getState();

          if (locState.result) {
            const { estimated_latitude, estimated_longitude, algorithm_applied, confidence_score, error_distance_m } = locState.result;
            logStageSuccess(
              `(${estimated_latitude.toFixed(4)}, ${estimated_longitude.toFixed(4)}) via ${algorithm_applied}`,
            );

            // Check for algorithm fallback
            if (algorithm_applied !== 'multilateration') {
              collectedWarnings.push(
                createWarning(
                  'algorithm_fallback',
                  'info',
                  'localizing',
                  'Algorithm Fallback',
                  `Localization fell back to "${algorithm_applied}" instead of the requested "multilateration" algorithm.`,
                ),
              );
              logStageWarning(`Algorithm fallback: ${algorithm_applied}`);
            }

            // Check for high error distance
            if (error_distance_m != null && error_distance_m > 500) {
              collectedWarnings.push(
                createWarning(
                  'high_error_distance',
                  'warning',
                  'localizing',
                  'High Error Distance',
                  `Localization error distance is ${error_distance_m.toFixed(1)}m, which exceeds the 500m threshold. Results may be unreliable.`,
                ),
              );
              logStageWarning(`High error distance: ${error_distance_m.toFixed(1)}m`);
            }

            // Check for low confidence from localization
            if (confidence_score < 0.5) {
              logStageWarning(`Low localization confidence: ${confidence_score.toFixed(2)}`);
            }
          }
        } catch (locErr) {
          const msg = locErr instanceof Error ? locErr.message : 'Localization failed';
          logStageError(`Localization failed: ${msg}`);
          collectedWarnings.push(
            createWarning(
              'stage_error',
              'danger',
              'localizing',
              'Localization Failed',
              `Localization engine returned an error: ${msg}. Downstream stages will continue.`,
            ),
          );
        }

        // ════════════════════════════════════════════════════════════════
        // STAGE 4: Tracking (Kalman)
        // ════════════════════════════════════════════════════════════════
        advanceStage('tracking');
        logStageStart('tracking');

        const trackingStore = useTrackingStore.getState();
        try {
          await trackingStore.runTracking(caseCode);
          const trackState = useTrackingStore.getState();

          if (trackState.result) {
            logStageSuccess(
              `${trackState.result.total_steps} steps, ${trackState.result.distance_km.toFixed(2)} km total`,
            );
          }
        } catch (trackErr) {
          const msg = trackErr instanceof Error ? trackErr.message : 'Tracking failed';
          logStageError(`Tracking failed: ${msg}`);
          collectedWarnings.push(
            createWarning(
              'stage_error',
              'warning',
              'tracking',
              'Tracking Unavailable',
              `Kalman tracking returned an error: ${msg}. Pipeline continues without path data.`,
            ),
          );
        }

        // ════════════════════════════════════════════════════════════════
        // STAGE 5: Confidence Analysis
        // ════════════════════════════════════════════════════════════════
        advanceStage('confidence');
        logStageStart('confidence');

        const confidenceStore = useConfidenceStore.getState();
        try {
          await confidenceStore.runConfidence(caseCode);
          const confState = useConfidenceStore.getState();

          if (confState.result) {
            const { confidence_score, confidence_level, gdop } = confState.result;
            logStageSuccess(`${confidence_score.toFixed(2)} ${confidence_level}`);

            if (confidence_score < 0.5) {
              collectedWarnings.push(
                createWarning(
                  'low_confidence',
                  'danger',
                  'confidence',
                  'Low Confidence Score',
                  `Confidence score is ${confidence_score.toFixed(2)} (${confidence_level}). Results should be interpreted with caution.`,
                ),
              );
              logStageWarning(`Low confidence: ${confidence_score.toFixed(2)}`);
            }

            if (gdop == null) {
              collectedWarnings.push(
                createWarning(
                  'stage_error',
                  'info',
                  'confidence',
                  'GDOP Unavailable',
                  'Geometric Dilution of Precision (GDOP) could not be computed. This may indicate insufficient tower geometry.',
                ),
              );
              logStageWarning('GDOP value is null');
            }
          }
        } catch (confErr) {
          const msg = confErr instanceof Error ? confErr.message : 'Confidence analysis failed';
          logStageError(`Confidence failed: ${msg}`);
          collectedWarnings.push(
            createWarning(
              'stage_error',
              'warning',
              'confidence',
              'Confidence Unavailable',
              `Confidence analysis returned an error: ${msg}.`,
            ),
          );
        }

        // ════════════════════════════════════════════════════════════════
        // STAGE 6: Evidence Audit
        // ════════════════════════════════════════════════════════════════
        advanceStage('evidence');
        logStageStart('evidence');

        const evidenceStore = useEvidenceStore.getState();
        try {
          await evidenceStore.fetchEvidence(caseCode);
          const evState = useEvidenceStore.getState();

          if (evState.evidence) {
            logStageSuccess(
              `Packet retrieved — ${evState.evidence.summary.total_measurements} measurements audited`,
            );
          }
        } catch (evErr) {
          const msg = evErr instanceof Error ? evErr.message : 'Evidence retrieval failed';
          logStageError(`Evidence failed: ${msg}`);
          collectedWarnings.push(
            createWarning(
              'stage_error',
              'info',
              'evidence',
              'Evidence Unavailable',
              `Evidence audit packet could not be retrieved: ${msg}.`,
            ),
          );
        }

        // ════════════════════════════════════════════════════════════════
        // PIPELINE COMPLETE
        // ════════════════════════════════════════════════════════════════
        const totalElapsed = Math.round(performance.now() - pipelineStart);

        set((s) => ({
          currentStage: 'complete',
          completedStages: [...s.completedStages, s.currentStage],
          warnings: collectedWarnings,
          isPipelineRunning: false,
          totalElapsedMs: totalElapsed,
        }));

        // ── Console: Pipeline Summary ────────────────────────────────
        console.log('─'.repeat(50));
        if (collectedWarnings.length > 0) {
          console.log(
            `%c⚠️ Warnings: ${collectedWarnings.length}`,
            'color: #fbbf24; font-weight: bold',
          );
          collectedWarnings.forEach((w) => {
            const icon = w.severity === 'danger' ? '🔴' : w.severity === 'warning' ? '🟡' : '🔵';
            console.log(`   ${icon} ${w.title}: ${w.message}`);
          });
        }
        console.log(
          `%c✅ Pipeline Complete (${totalElapsed.toLocaleString()}ms)`,
          'color: #34d399; font-weight: bold; font-size: 13px',
        );
        console.groupEnd();
      } catch (fatalErr) {
        // ── Fatal error — pipeline cannot continue ───────────────────
        const totalElapsed = Math.round(performance.now() - pipelineStart);
        const message =
          fatalErr instanceof Error ? fatalErr.message : 'Pipeline failed unexpectedly';

        set((s) => ({
          currentStage: 'failed',
          completedStages: [...s.completedStages, s.currentStage],
          warnings: collectedWarnings,
          pipelineError: message,
          isPipelineRunning: false,
          totalElapsedMs: totalElapsed,
        }));

        logStageError(`FATAL: ${message}`);
        console.log(
          `%c❌ Pipeline Failed (${totalElapsed.toLocaleString()}ms)`,
          'color: #f87171; font-weight: bold; font-size: 13px',
        );
        console.groupEnd();
      }
    },

    // ── Clear Pipeline ──────────────────────────────────────────────────
    clearPipeline: () => {
      set({ ...INITIAL_STATE });

      // Also clear all downstream stores
      useSimulationStore.getState().clearResults();
      useValidationStore.getState().clearValidation();
      useLocalizationStore.getState().clearResults();
      useTrackingStore.getState().clearResults();
      useConfidenceStore.getState().clearResults();
      useEvidenceStore.getState().clearEvidence();
    },

    // ── Dismiss Warning ─────────────────────────────────────────────────
    dismissWarning: (warningId) => {
      set((s) => ({
        warnings: s.warnings.map((w) =>
          w.id === warningId ? { ...w, dismissed: true } : w,
        ),
      }));
    },
  }),
);
