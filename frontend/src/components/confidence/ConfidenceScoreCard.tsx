import {
  ShieldCheck,
  ShieldAlert,
  Gauge,
  Clock,
  Target,
  Crosshair,
  AlertTriangle,
} from 'lucide-react';
import { cn } from '@/lib/cn';
import { useConfidenceStore } from '@/stores/confidenceStore';
import { Badge } from '@/components/ui';

// ── Helpers ─────────────────────────────────────────────────────────────

function classifyConfidence(score: number): {
  text: string;
  variant: 'success' | 'warning' | 'danger';
} {
  const pct = score * 100;
  if (pct >= 80) return { text: 'High', variant: 'success' };
  if (pct >= 50) return { text: 'Medium', variant: 'warning' };
  return { text: 'Low', variant: 'danger' };
}

function confidenceBarColor(score: number): string {
  const pct = score * 100;
  if (pct >= 80) return 'bg-success';
  if (pct >= 50) return 'bg-warning';
  return 'bg-danger';
}

// ── Component ───────────────────────────────────────────────────────────

interface ConfidenceScoreCardProps {
  className?: string;
}

/**
 * Glassmorphic confidence analysis result card.
 *
 * Displays:
 *   - Confidence score (0–100%) with animated progress bar
 *   - Classification badge (High / Medium / Low)
 *   - GDOP, method, computation time stat tiles
 *   - Error ellipse parameters (semi-major, semi-minor, orientation)
 *
 * Reads directly from `useConfidenceStore`.
 */
export function ConfidenceScoreCard({ className }: ConfidenceScoreCardProps) {
  const { result, isRunning, error } = useConfidenceStore();

  // ── Nothing to render ──────────────────────────────────────────────
  if (!result && !isRunning && !error) return null;

  const classification = result ? classifyConfidence(result.confidence_score) : null;

  return (
    <section
      id="confidence-score-card"
      className={cn('glass-card rounded-2xl p-6 animate-fade-in', className)}
    >
      {/* ── Header ───────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <div
            className={cn(
              'h-10 w-10 rounded-xl flex items-center justify-center border',
              result && classification
                ? classification.variant === 'success'
                  ? 'bg-success/12 border-success/20'
                  : classification.variant === 'warning'
                    ? 'bg-warning/12 border-warning/20'
                    : 'bg-danger/12 border-danger/20'
                : 'bg-brand-primary/12 border-brand-primary/20',
            )}
          >
            {result && classification && classification.variant === 'success' ? (
              <ShieldCheck className="h-5 w-5 text-success" />
            ) : result && classification ? (
              <ShieldAlert className="h-5 w-5 text-warning" />
            ) : (
              <ShieldCheck className="h-5 w-5 text-brand-primary" />
            )}
          </div>
          <div>
            <h3 className="text-base font-bold text-content-primary">
              Confidence Analysis
            </h3>
            <p className="text-xs text-content-tertiary mt-0.5">
              {isRunning
                ? 'Computing confidence metrics…'
                : result
                  ? `${result.method} — ${result.case_code}`
                  : 'Confidence analysis failed'}
            </p>
          </div>
        </div>

        {/* Status badge */}
        {!isRunning && result && classification && (
          <Badge variant={classification.variant} dot>
            {classification.text} Confidence
          </Badge>
        )}
      </div>

      {/* ── Shimmer while loading ──────────────────────────────────── */}
      {isRunning && (
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
      {!isRunning && error && (
        <div className="bg-danger/8 border border-danger/20 rounded-xl p-4 flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-danger shrink-0 mt-0.5" />
          <p className="text-sm text-danger leading-relaxed">{error}</p>
        </div>
      )}

      {/* ── Result content ─────────────────────────────────────────── */}
      {!isRunning && result && (
        <>
          {/* Primary stat tiles — 4 column */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
            {/* Confidence Score with progress bar */}
            <div className="rounded-xl border border-border-primary bg-surface-secondary/50 px-4 py-3">
              <div className="flex items-center gap-2 mb-2">
                <Gauge className="h-4 w-4 text-content-tertiary" />
                <span className="text-[10px] uppercase tracking-wider font-semibold text-content-tertiary">
                  Score
                </span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-2xl font-bold tabular-nums text-content-primary">
                  {(result.confidence_score * 100).toFixed(0)}%
                </span>
                <div className="flex-1 h-2 rounded-full bg-surface-tertiary overflow-hidden">
                  <div
                    className={cn(
                      'h-full rounded-full transition-all duration-700 ease-out',
                      confidenceBarColor(result.confidence_score),
                    )}
                    style={{ width: `${result.confidence_score * 100}%` }}
                  />
                </div>
              </div>
            </div>

            <StatTile
              icon={<Target className="h-4 w-4 text-info" />}
              label="GDOP"
              value={result.gdop != null ? result.gdop.toFixed(2) : '—'}
            />
            <StatTile
              icon={<Crosshair className="h-4 w-4 text-brand-primary" />}
              label="Method"
              value={result.method}
            />
            <StatTile
              icon={<Clock className="h-4 w-4 text-content-tertiary" />}
              label="Compute Time"
              value={`${result.computation_time_ms.toFixed(0)} ms`}
            />
          </div>

          {/* Error Ellipse — 3 column */}
          <div>
            <h4 className="text-xs font-semibold text-content-tertiary uppercase tracking-wider mb-2">
              Error Ellipse
            </h4>
            <div className="grid grid-cols-3 gap-3">
              <EllipseTile
                label="Semi-Major"
                value={result.error_ellipse_semi_major_m}
                unit="m"
              />
              <EllipseTile
                label="Semi-Minor"
                value={result.error_ellipse_semi_minor_m}
                unit="m"
              />
              <EllipseTile
                label="Orientation"
                value={result.error_ellipse_orientation_deg}
                unit="°"
              />
            </div>
          </div>
        </>
      )}
    </section>
  );
}

// ── Internal sub-components ─────────────────────────────────────────────

interface StatTileProps {
  icon: React.ReactNode;
  label: string;
  value: string;
}

function StatTile({ icon, label, value }: StatTileProps) {
  return (
    <div className="rounded-xl border border-border-primary bg-surface-secondary/50 px-4 py-3 flex flex-col gap-1">
      <div className="flex items-center gap-2">
        {icon}
        <span className="text-[10px] uppercase tracking-wider font-semibold text-content-tertiary">
          {label}
        </span>
      </div>
      <span className="text-lg font-bold text-content-primary truncate" title={value}>
        {value}
      </span>
    </div>
  );
}

interface EllipseTileProps {
  label: string;
  value: number | null;
  unit: string;
}

function EllipseTile({ label, value, unit }: EllipseTileProps) {
  return (
    <div className="rounded-xl border border-border-primary bg-surface-secondary/50 px-4 py-3 flex flex-col gap-1">
      <span className="text-[10px] uppercase tracking-wider font-semibold text-content-tertiary">
        {label}
      </span>
      <span className="text-lg font-bold tabular-nums text-content-primary">
        {value != null ? `${value.toFixed(1)}${unit}` : '—'}
      </span>
    </div>
  );
}
