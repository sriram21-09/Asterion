import {
  Zap,
  ShieldCheck,
  Crosshair,
  Navigation,
  Shield,
  FileCheck,
  CheckCircle,
  XCircle,
  Loader2,
} from 'lucide-react';
import { cn } from '@/lib/cn';
import { usePipelineCoordinator } from '@/stores/pipelineCoordinator';
import type { PipelineStage } from '@/stores/pipelineCoordinator';

// ── Stage Definition ────────────────────────────────────────────────────

interface StageConfig {
  key: PipelineStage;
  label: string;
  icon: React.FC<{ className?: string }>;
}

const PIPELINE_STAGES: StageConfig[] = [
  { key: 'simulating', label: 'Simulate', icon: Zap },
  { key: 'validating', label: 'Validate', icon: ShieldCheck },
  { key: 'localizing', label: 'Localize', icon: Crosshair },
  { key: 'tracking', label: 'Track', icon: Navigation },
  { key: 'confidence', label: 'Confidence', icon: Shield },
  { key: 'evidence', label: 'Evidence', icon: FileCheck },
];

// ── Component ───────────────────────────────────────────────────────────

interface PipelineProgressProps {
  className?: string;
}

/**
 * Horizontal stepper / progress indicator for the pipeline.
 *
 * Shows 6 connected stage dots with:
 *   - Current stage: brand color + pulse animation
 *   - Completed stages: success checkmark
 *   - Failed pipeline: danger X on the failed stage
 *   - Upcoming stages: muted appearance
 */
export function PipelineProgress({ className }: PipelineProgressProps) {
  const { currentStage, completedStages, isPipelineRunning, totalElapsedMs } =
    usePipelineCoordinator();

  // Don't render when pipeline hasn't been started
  if (currentStage === 'idle') {
    return null;
  }

  const isComplete = currentStage === 'complete';
  const isFailed = currentStage === 'failed';

  /**
   * Determine the status of each stage dot.
   */
  const getStageStatus = (
    stageKey: PipelineStage,
  ): 'completed' | 'active' | 'failed' | 'upcoming' => {
    if (completedStages.includes(stageKey)) return 'completed';
    if (stageKey === currentStage) {
      return isFailed ? 'failed' : 'active';
    }
    // If pipeline is complete, mark all stages as completed
    if (isComplete) return 'completed';
    return 'upcoming';
  };

  return (
    <section
      id="pipeline-progress"
      className={cn(
        'glass-card rounded-2xl px-6 py-5 animate-fade-in',
        className,
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-2">
          {isPipelineRunning ? (
            <Loader2 className="h-4 w-4 text-brand-primary animate-spin" />
          ) : isComplete ? (
            <CheckCircle className="h-4 w-4 text-success" />
          ) : isFailed ? (
            <XCircle className="h-4 w-4 text-danger" />
          ) : null}
          <h3 className="text-xs font-semibold uppercase tracking-wider text-content-tertiary">
            {isPipelineRunning
              ? 'Pipeline Running'
              : isComplete
                ? 'Pipeline Complete'
                : isFailed
                  ? 'Pipeline Failed'
                  : 'Pipeline'}
          </h3>
        </div>

        {totalElapsedMs > 0 && (
          <span className="text-xs font-mono text-content-tertiary">
            {totalElapsedMs >= 1000
              ? `${(totalElapsedMs / 1000).toFixed(1)}s`
              : `${totalElapsedMs}ms`}
          </span>
        )}
      </div>

      {/* Stepper */}
      <div className="flex items-center justify-between relative">
        {/* Connection line */}
        <div className="absolute top-5 left-[calc(8.33%+16px)] right-[calc(8.33%+16px)] h-0.5 bg-border-primary">
          {/* Filled progress line */}
          <div
            className={cn(
              'absolute inset-y-0 left-0 transition-all duration-500 ease-out rounded-full',
              isFailed ? 'bg-danger' : 'bg-brand-primary',
            )}
            style={{
              width: `${getProgressWidth(currentStage, completedStages)}%`,
            }}
          />
        </div>

        {/* Stage dots */}
        {PIPELINE_STAGES.map((stage) => {
          const status = getStageStatus(stage.key);
          const Icon = stage.icon;

          return (
            <div
              key={stage.key}
              className="flex flex-col items-center gap-2 relative z-10"
              style={{ flex: '1 1 0%' }}
            >
              {/* Dot */}
              <div
                className={cn(
                  'h-10 w-10 rounded-xl flex items-center justify-center transition-all duration-300 border',
                  status === 'completed' &&
                    'bg-success/12 border-success/25 text-success',
                  status === 'active' &&
                    'bg-brand-primary/15 border-brand-primary/30 text-brand-primary shadow-lg shadow-brand-primary/10',
                  status === 'failed' &&
                    'bg-danger/12 border-danger/25 text-danger',
                  status === 'upcoming' &&
                    'bg-surface-secondary border-border-primary text-content-tertiary',
                )}
              >
                {status === 'completed' ? (
                  <CheckCircle className="h-4.5 w-4.5" />
                ) : status === 'active' ? (
                  <div className="relative">
                    <Icon className="h-4.5 w-4.5" />
                    {/* Pulse ring */}
                    <span className="absolute -inset-1.5 rounded-xl border-2 border-brand-primary/40 animate-ping" />
                  </div>
                ) : status === 'failed' ? (
                  <XCircle className="h-4.5 w-4.5" />
                ) : (
                  <Icon className="h-4.5 w-4.5" />
                )}
              </div>

              {/* Label */}
              <span
                className={cn(
                  'text-[10px] font-semibold uppercase tracking-wider transition-colors duration-300',
                  status === 'completed' && 'text-success',
                  status === 'active' && 'text-brand-primary',
                  status === 'failed' && 'text-danger',
                  status === 'upcoming' && 'text-content-tertiary',
                )}
              >
                {stage.label}
              </span>
            </div>
          );
        })}
      </div>
    </section>
  );
}

// ── Helper: Progress Bar Width ──────────────────────────────────────────

function getProgressWidth(
  currentStage: PipelineStage,
  completedStages: PipelineStage[],
): number {
  const stageOrder: PipelineStage[] = [
    'simulating',
    'validating',
    'localizing',
    'tracking',
    'confidence',
    'evidence',
  ];

  if (currentStage === 'complete') return 100;
  if (currentStage === 'idle') return 0;

  const currentIdx = stageOrder.indexOf(currentStage);
  if (currentIdx === -1) {
    // Failed state — use completedStages to determine width
    const maxCompleted = Math.max(
      ...completedStages.map((s) => stageOrder.indexOf(s)),
      0,
    );
    return (maxCompleted / (stageOrder.length - 1)) * 100;
  }

  return (currentIdx / (stageOrder.length - 1)) * 100;
}
