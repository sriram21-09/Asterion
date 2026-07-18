import {
  AlertTriangle,
  RefreshCw,
  ShieldAlert,
  Info,
  X,
  ShieldX,
  MapPinOff,
} from 'lucide-react';
import { cn } from '@/lib/cn';
import { usePipelineCoordinator } from '@/stores/pipelineCoordinator';
import type { WarningCategory, WarningSeverity } from '@/stores/pipelineCoordinator';

// ── Category Config ─────────────────────────────────────────────────────

const CATEGORY_CONFIG: Record<
  WarningCategory,
  {
    icon: React.FC<{ className?: string }>;
    label: string;
  }
> = {
  validation_failure: { icon: ShieldX, label: 'Validation' },
  validation_warning: { icon: AlertTriangle, label: 'Validation' },
  algorithm_fallback: { icon: RefreshCw, label: 'Algorithm' },
  low_confidence: { icon: ShieldAlert, label: 'Confidence' },
  high_error_distance: { icon: MapPinOff, label: 'Accuracy' },
  stage_error: { icon: Info, label: 'Pipeline' },
};

const SEVERITY_STYLES: Record<
  WarningSeverity,
  {
    card: string;
    icon: string;
    badge: string;
    badgeText: string;
  }
> = {
  danger: {
    card: 'bg-danger/6 border-danger/20 hover:border-danger/35',
    icon: 'text-danger',
    badge: 'bg-danger/12 text-danger border-danger/25',
    badgeText: 'Critical',
  },
  warning: {
    card: 'bg-warning/6 border-warning/20 hover:border-warning/35',
    icon: 'text-warning',
    badge: 'bg-warning/12 text-warning border-warning/25',
    badgeText: 'Warning',
  },
  info: {
    card: 'bg-info/6 border-info/20 hover:border-info/35',
    icon: 'text-info',
    badge: 'bg-info/12 text-info border-info/25',
    badgeText: 'Info',
  },
};

// ── Component ───────────────────────────────────────────────────────────

interface PipelineWarningCardsProps {
  className?: string;
}

/**
 * Renders glassmorphic warning cards collected during a pipeline run.
 *
 * Categories:
 *   - Validation failures/warnings (amber/orange)
 *   - Algorithm fallback (blue/info)
 *   - Low confidence (red/danger)
 *   - Non-blocking stage errors (gray/info)
 *
 * Each card is individually dismissible and animates in with a stagger.
 */
export function PipelineWarningCards({ className }: PipelineWarningCardsProps) {
  const { warnings, dismissWarning, currentStage } = usePipelineCoordinator();

  const activeWarnings = warnings.filter((w) => !w.dismissed);

  if (activeWarnings.length === 0 || currentStage === 'idle') {
    return null;
  }

  return (
    <section
      id="pipeline-warnings"
      className={cn('space-y-3', className)}
    >
      {/* Section Header */}
      <div className="flex items-center gap-2 mb-1">
        <AlertTriangle className="h-4 w-4 text-warning" />
        <h3 className="text-xs font-semibold uppercase tracking-wider text-content-tertiary">
          Pipeline Alerts ({activeWarnings.length})
        </h3>
      </div>

      {/* Warning Cards */}
      {activeWarnings.map((warning, idx) => {
        const catConfig = CATEGORY_CONFIG[warning.category];
        const sevStyles = SEVERITY_STYLES[warning.severity];
        const Icon = catConfig.icon;

        return (
          <div
            key={warning.id}
            className={cn(
              'relative rounded-xl border p-4 transition-all duration-200',
              'animate-slide-up',
              sevStyles.card,
            )}
            style={{ animationDelay: `${idx * 80}ms` }}
          >
            {/* Dismiss button */}
            <button
              onClick={() => dismissWarning(warning.id)}
              className="absolute top-3 right-3 p-1 rounded-lg text-content-tertiary hover:text-content-primary hover:bg-surface-secondary/50 transition-colors"
              title="Dismiss"
            >
              <X className="h-3.5 w-3.5" />
            </button>

            <div className="flex items-start gap-3 pr-6">
              {/* Icon */}
              <div
                className={cn(
                  'h-9 w-9 rounded-lg flex items-center justify-center shrink-0',
                  sevStyles.card,
                )}
              >
                <Icon className={cn('h-4.5 w-4.5', sevStyles.icon)} />
              </div>

              {/* Content */}
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 flex-wrap mb-1">
                  <span className="text-sm font-semibold text-content-primary">
                    {warning.title}
                  </span>
                  <span
                    className={cn(
                      'inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider border',
                      sevStyles.badge,
                    )}
                  >
                    {sevStyles.badgeText}
                  </span>
                  <span className="text-[10px] font-medium text-content-tertiary uppercase tracking-wider">
                    {catConfig.label}
                  </span>
                </div>
                <p className="text-xs text-content-secondary leading-relaxed">
                  {warning.message}
                </p>
              </div>
            </div>
          </div>
        );
      })}
    </section>
  );
}
