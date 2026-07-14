import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  ShieldCheck,
  ShieldX,
  FileWarning,
} from 'lucide-react';
import { cn } from '@/lib/cn';
import { useValidationStore } from '@/stores/validationStore';
import { Badge } from '@/components/ui';

// ── Helpers ─────────────────────────────────────────────────────────────

const SEVERITY_CONFIG = {
  error: {
    icon: XCircle,
    label: 'Error',
    badgeVariant: 'danger' as const,
    rowClass: 'bg-danger/5 border-danger/15',
    iconClass: 'text-danger',
  },
  warning: {
    icon: AlertTriangle,
    label: 'Warning',
    badgeVariant: 'warning' as const,
    rowClass: 'bg-warning/5 border-warning/15',
    iconClass: 'text-warning',
  },
} as const;

// ── Component ───────────────────────────────────────────────────────────

interface ValidationSummaryProps {
  className?: string;
}

/**
 * Static validation summary card.
 *
 * Renders a glassmorphic panel showing:
 *   - Overall Valid / Invalid status
 *   - Validated, rejected, and warning counters
 *   - A scrollable table of structured errors
 *
 * The component reads directly from `useValidationStore`, so it reacts
 * automatically whenever validation runs.
 */
export function ValidationSummary({ className }: ValidationSummaryProps) {
  const {
    isValid,
    validCount,
    rejectedCount,
    warningCount,
    errors,
    isValidating,
    validationError,
  } = useValidationStore();

  // ── Nothing to show yet ─────────────────────────────────────────────
  if (isValid === null && !isValidating && !validationError) {
    return null;
  }

  const totalChecked = validCount + rejectedCount;

  return (
    <section
      id="validation-summary"
      className={cn(
        'glass-card rounded-2xl p-6 animate-fade-in',
        className,
      )}
    >
      {/* ── Header ─────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          {isValid ? (
            <div className="h-10 w-10 rounded-xl bg-success/12 border border-success/20 flex items-center justify-center">
              <ShieldCheck className="h-5 w-5 text-success" />
            </div>
          ) : (
            <div className="h-10 w-10 rounded-xl bg-danger/12 border border-danger/20 flex items-center justify-center">
              <ShieldX className="h-5 w-5 text-danger" />
            </div>
          )}
          <div>
            <h3 className="text-base font-bold text-content-primary">
              Validation Summary
            </h3>
            <p className="text-xs text-content-tertiary mt-0.5">
              {isValidating
                ? 'Validating measurements…'
                : isValid
                  ? 'All measurements passed validation'
                  : `${rejectedCount} measurement(s) rejected`}
            </p>
          </div>
        </div>

        {/* Overall badge */}
        {!isValidating && isValid !== null && (
          <Badge variant={isValid ? 'success' : 'danger'} dot>
            {isValid ? 'Valid' : 'Invalid'}
          </Badge>
        )}
      </div>

      {/* ── Shimmer while loading ──────────────────────────────────── */}
      {isValidating && (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-10 rounded-xl skeleton-shimmer"
              style={{ animationDelay: `${i * 0.15}s` }}
            />
          ))}
        </div>
      )}

      {/* ── API-level error ────────────────────────────────────────── */}
      {!isValidating && validationError && (
        <div className="bg-danger/8 border border-danger/20 rounded-xl p-4 flex items-start gap-3">
          <FileWarning className="h-5 w-5 text-danger shrink-0 mt-0.5" />
          <p className="text-sm text-danger leading-relaxed">
            {validationError}
          </p>
        </div>
      )}

      {/* ── Result stats + error list ──────────────────────────────── */}
      {!isValidating && isValid !== null && (
        <>
          {/* Stat counters */}
          <div className="grid grid-cols-3 gap-3 mb-5">
            <StatTile
              label="Checked"
              value={totalChecked}
              icon={<CheckCircle className="h-4 w-4 text-brand-primary" />}
            />
            <StatTile
              label="Rejected"
              value={rejectedCount}
              icon={<XCircle className="h-4 w-4 text-danger" />}
              danger={rejectedCount > 0}
            />
            <StatTile
              label="Warnings"
              value={warningCount}
              icon={<AlertTriangle className="h-4 w-4 text-warning" />}
              warn={warningCount > 0}
            />
          </div>

          {/* Error list */}
          {errors.length > 0 && (
            <div className="space-y-1.5">
              <h4 className="text-xs font-semibold text-content-tertiary uppercase tracking-wider mb-2">
                Issues ({errors.length})
              </h4>

              <div className="max-h-64 overflow-y-auto rounded-xl border border-border-primary divide-y divide-border-primary">
                {errors.map((err, idx) => {
                  const cfg = SEVERITY_CONFIG[err.severity];
                  const Icon = cfg.icon;
                  return (
                    <div
                      key={`${err.measurement_index}-${err.field}-${idx}`}
                      className={cn(
                        'flex items-start gap-3 px-4 py-3 transition-colors hover:brightness-110',
                        cfg.rowClass,
                      )}
                    >
                      <Icon className={cn('h-4 w-4 shrink-0 mt-0.5', cfg.iconClass)} />
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-xs font-mono font-semibold text-content-secondary">
                            #{err.measurement_index}
                          </span>
                          <Badge variant={cfg.badgeVariant} className="text-[10px]">
                            {cfg.label}
                          </Badge>
                          <span className="text-xs font-medium text-content-tertiary">
                            {err.field}
                          </span>
                        </div>
                        <p className="text-sm text-content-secondary mt-1 leading-snug">
                          {err.message}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* All-clear message when no issues */}
          {errors.length === 0 && (
            <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-success/6 border border-success/15">
              <CheckCircle className="h-5 w-5 text-success shrink-0" />
              <p className="text-sm text-success font-medium">
                All {totalChecked} measurement(s) passed validation — no issues found.
              </p>
            </div>
          )}
        </>
      )}
    </section>
  );
}

// ── Internal sub-component ──────────────────────────────────────────────

interface StatTileProps {
  label: string;
  value: number;
  icon: React.ReactNode;
  danger?: boolean;
  warn?: boolean;
}

function StatTile({ label, value, icon, danger, warn }: StatTileProps) {
  return (
    <div
      className={cn(
        'rounded-xl border px-4 py-3 flex flex-col gap-1 transition-colors',
        danger
          ? 'border-danger/20 bg-danger/5'
          : warn
            ? 'border-warning/20 bg-warning/5'
            : 'border-border-primary bg-surface-secondary/50',
      )}
    >
      <div className="flex items-center gap-2">
        {icon}
        <span className="text-[10px] uppercase tracking-wider font-semibold text-content-tertiary">
          {label}
        </span>
      </div>
      <span
        className={cn(
          'text-2xl font-bold tabular-nums',
          danger
            ? 'text-danger'
            : warn
              ? 'text-warning'
              : 'text-content-primary',
        )}
      >
        {value}
      </span>
    </div>
  );
}
