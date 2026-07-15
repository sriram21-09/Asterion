import {
  Crosshair,
  MapPin,
  Signal,
  Clock,
  Gauge,
  Target,
  AlertTriangle,
} from 'lucide-react';
import { cn } from '@/lib/cn';
import { useLocalizationStore } from '@/stores/localizationStore';
import { Badge } from '@/components/ui';

// ── Helpers ─────────────────────────────────────────────────────────────

function confidenceLabel(score: number): { text: string; variant: 'success' | 'warning' | 'danger' } {
  if (score >= 0.8) return { text: 'High', variant: 'success' };
  if (score >= 0.5) return { text: 'Medium', variant: 'warning' };
  return { text: 'Low', variant: 'danger' };
}

function formatDistance(metres: number): string {
  if (metres >= 1000) return `${(metres / 1000).toFixed(2)} km`;
  return `${metres.toFixed(1)} m`;
}

// ── Component ───────────────────────────────────────────────────────────

interface LocalizationResultCardProps {
  className?: string;
}

/**
 * Glassmorphic result card for the localization engine output.
 *
 * Displays:
 *   - Estimated latitude & longitude
 *   - Error distance (metres) — computed via Haversine when expected coords are known
 *   - Number of signals used
 *   - Algorithm applied
 *   - Confidence score (progress arc)
 *   - Time elapsed
 *
 * Reads directly from `useLocalizationStore`.
 */
export function LocalizationResultCard({ className }: LocalizationResultCardProps) {
  const { result, isRunning, error } = useLocalizationStore();

  // ── Nothing to render ──────────────────────────────────────────────
  if (!result && !isRunning && !error) return null;

  return (
    <section
      id="localization-result"
      className={cn('glass-card rounded-2xl p-6 animate-fade-in', className)}
    >
      {/* ── Header ───────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-brand-primary/12 border border-brand-primary/20 flex items-center justify-center">
            <Crosshair className="h-5 w-5 text-brand-primary" />
          </div>
          <div>
            <h3 className="text-base font-bold text-content-primary">
              Localization Result
            </h3>
            <p className="text-xs text-content-tertiary mt-0.5">
              {isRunning
                ? 'Computing device position…'
                : result
                  ? `${result.algorithm_applied} — ${result.signals_used} signal(s)`
                  : 'Localization failed'}
            </p>
          </div>
        </div>

        {/* Status badge */}
        {!isRunning && result && (
          <Badge
            variant={confidenceLabel(result.confidence_score).variant}
            dot
          >
            {confidenceLabel(result.confidence_score).text} Confidence
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

      {/* ── Result grid ───────────────────────────────────────────── */}
      {!isRunning && result && (
        <>
          {/* Primary stats — 2-column on mobile, 4-column on large */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
            <ResultTile
              icon={<MapPin className="h-4 w-4 text-brand-primary" />}
              label="Latitude"
              value={result.estimated_latitude.toFixed(6)}
              mono
            />
            <ResultTile
              icon={<MapPin className="h-4 w-4 text-brand-primary" />}
              label="Longitude"
              value={result.estimated_longitude.toFixed(6)}
              mono
            />
            <ResultTile
              icon={<Signal className="h-4 w-4 text-info" />}
              label="Signals Used"
              value={String(result.signals_used)}
            />
            <ResultTile
              icon={<Clock className="h-4 w-4 text-content-tertiary" />}
              label="Time Elapsed"
              value={`${result.time_elapsed_ms} ms`}
            />
          </div>

          {/* Secondary row */}
          <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
            {/* Confidence progress */}
            <div className="rounded-xl border border-border-primary bg-surface-secondary/50 px-4 py-3">
              <div className="flex items-center gap-2 mb-2">
                <Gauge className="h-4 w-4 text-content-tertiary" />
                <span className="text-[10px] uppercase tracking-wider font-semibold text-content-tertiary">
                  Confidence
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
                      result.confidence_score >= 0.8
                        ? 'bg-success'
                        : result.confidence_score >= 0.5
                          ? 'bg-warning'
                          : 'bg-danger',
                    )}
                    style={{ width: `${result.confidence_score * 100}%` }}
                  />
                </div>
              </div>
            </div>

            {/* Error distance */}
            <div className="rounded-xl border border-border-primary bg-surface-secondary/50 px-4 py-3">
              <div className="flex items-center gap-2 mb-2">
                <Target className="h-4 w-4 text-content-tertiary" />
                <span className="text-[10px] uppercase tracking-wider font-semibold text-content-tertiary">
                  Error Distance
                </span>
              </div>
              <span
                className={cn(
                  'text-2xl font-bold tabular-nums',
                  result.error_distance_m == null
                    ? 'text-content-tertiary'
                    : result.error_distance_m <= 50
                      ? 'text-success'
                      : result.error_distance_m <= 200
                        ? 'text-warning'
                        : 'text-danger',
                )}
              >
                {result.error_distance_m != null
                  ? formatDistance(result.error_distance_m)
                  : '—'}
              </span>
              {result.error_distance_m == null && (
                <p className="text-[10px] text-content-tertiary mt-1">
                  No expected coordinates provided
                </p>
              )}
            </div>

            {/* Algorithm badge */}
            <div className="rounded-xl border border-border-primary bg-surface-secondary/50 px-4 py-3 flex flex-col justify-between">
              <div className="flex items-center gap-2 mb-2">
                <Crosshair className="h-4 w-4 text-content-tertiary" />
                <span className="text-[10px] uppercase tracking-wider font-semibold text-content-tertiary">
                  Algorithm
                </span>
              </div>
              <Badge variant="info" className="w-fit">
                {result.algorithm_applied}
              </Badge>
            </div>
          </div>
        </>
      )}
    </section>
  );
}

// ── Internal sub-component ──────────────────────────────────────────────

interface ResultTileProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  mono?: boolean;
}

function ResultTile({ icon, label, value, mono }: ResultTileProps) {
  return (
    <div className="rounded-xl border border-border-primary bg-surface-secondary/50 px-4 py-3 flex flex-col gap-1">
      <div className="flex items-center gap-2">
        {icon}
        <span className="text-[10px] uppercase tracking-wider font-semibold text-content-tertiary">
          {label}
        </span>
      </div>
      <span
        className={cn(
          'text-lg font-bold text-content-primary truncate',
          mono && 'font-mono text-base',
        )}
        title={value}
      >
        {value}
      </span>
    </div>
  );
}
