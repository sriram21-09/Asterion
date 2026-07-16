import {
  Navigation,
  MapPin,
  Gauge,
  Clock,
  Hash,
  Route,
  Timer,
  AlertTriangle,
} from 'lucide-react';
import { cn } from '@/lib/cn';
import { useTrackingStore } from '@/stores/trackingStore';
import { Badge } from '@/components/ui';

// ── Helpers ─────────────────────────────────────────────────────────────

function velocityColor(v: number): string {
  if (v <= 30) return 'text-emerald-400';
  if (v <= 80) return 'text-amber-400';
  if (v <= 120) return 'text-orange-400';
  return 'text-red-400';
}

function velocityLabel(v: number): string {
  if (v <= 30) return 'Slow';
  if (v <= 80) return 'Moderate';
  if (v <= 120) return 'Fast';
  return 'Very Fast';
}

// ── Component ───────────────────────────────────────────────────────────

interface TrackingPathTableProps {
  className?: string;
}

/**
 * Glassmorphic tracking path table card.
 *
 * Displays:
 *   - Summary stats: total steps, distance, avg velocity, computation time
 *   - Chronological table: Step #, Lat, Lon, Velocity (km/h), Timestamp
 *   - Velocity colour coding by speed band
 *
 * Reads directly from `useTrackingStore`.
 */
export function TrackingPathTable({ className }: TrackingPathTableProps) {
  const { result, isRunning, error } = useTrackingStore();

  // ── Nothing to render ──────────────────────────────────────────────
  if (!result && !isRunning && !error) return null;

  return (
    <section
      id="tracking-path-table"
      className={cn('glass-card rounded-2xl p-6 animate-fade-in', className)}
    >
      {/* ── Header ───────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-brand-primary/12 border border-brand-primary/20 flex items-center justify-center">
            <Navigation className="h-5 w-5 text-brand-primary" />
          </div>
          <div>
            <h3 className="text-base font-bold text-content-primary">
              Tracking Path
            </h3>
            <p className="text-xs text-content-tertiary mt-0.5">
              {isRunning
                ? 'Computing smoothed path…'
                : result
                  ? `${result.total_steps} step(s) — ${result.case_code}`
                  : 'Tracking failed'}
            </p>
          </div>
        </div>

        {/* Status badge */}
        {!isRunning && result && (
          <Badge
            variant={result.total_steps > 0 ? 'success' : 'warning'}
            dot
          >
            {result.total_steps > 0
              ? `${result.total_steps} Steps`
              : 'No Path'}
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
          {/* Summary stat tiles — 4 column */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
            <StatTile
              icon={<Hash className="h-4 w-4 text-brand-primary" />}
              label="Total Steps"
              value={String(result.total_steps)}
            />
            <StatTile
              icon={<Route className="h-4 w-4 text-info" />}
              label="Distance"
              value={`${result.distance_km.toFixed(2)} km`}
            />
            <StatTile
              icon={<Gauge className="h-4 w-4 text-warning" />}
              label="Avg Velocity"
              value={`${result.avg_velocity_kmh.toFixed(1)} km/h`}
            />
            <StatTile
              icon={<Timer className="h-4 w-4 text-content-tertiary" />}
              label="Compute Time"
              value={`${result.computation_time_ms} ms`}
            />
          </div>

          {/* Path table */}
          {result.path.length > 0 ? (
            <div className="rounded-xl border border-border-primary overflow-hidden">
              <div className="overflow-x-auto max-h-96 overflow-y-auto">
                <table
                  id="tracking-path-data-table"
                  className="w-full text-left text-sm text-content-secondary"
                >
                  <thead className="bg-surface-secondary text-xs uppercase text-content-tertiary border-b border-border-primary sticky top-0 z-10">
                    <tr>
                      <th className="px-5 py-3.5 font-semibold">
                        <span className="inline-flex items-center space-x-1.5">
                          <Hash className="w-3.5 h-3.5" />
                          <span>Step</span>
                        </span>
                      </th>
                      <th className="px-5 py-3.5 font-semibold">
                        <span className="inline-flex items-center space-x-1.5">
                          <MapPin className="w-3.5 h-3.5" />
                          <span>Latitude</span>
                        </span>
                      </th>
                      <th className="px-5 py-3.5 font-semibold">
                        <span className="inline-flex items-center space-x-1.5">
                          <MapPin className="w-3.5 h-3.5" />
                          <span>Longitude</span>
                        </span>
                      </th>
                      <th className="px-5 py-3.5 font-semibold">
                        <span className="inline-flex items-center space-x-1.5">
                          <Gauge className="w-3.5 h-3.5" />
                          <span>Velocity (km/h)</span>
                        </span>
                      </th>
                      <th className="px-5 py-3.5 font-semibold">
                        <span className="inline-flex items-center space-x-1.5">
                          <Clock className="w-3.5 h-3.5" />
                          <span>Timestamp</span>
                        </span>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.path.map((step, idx) => (
                      <tr
                        key={step.step_number}
                        className={cn(
                          'border-b border-border-secondary hover:bg-surface-secondary/50 transition-colors',
                          idx % 2 !== 0 && 'bg-surface-secondary/20',
                        )}
                      >
                        <td className="px-5 py-3 font-mono text-xs text-content-primary font-medium">
                          <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-brand-primary/10 text-brand-primary text-xs font-semibold">
                            #{step.step_number}
                          </span>
                        </td>
                        <td className="px-5 py-3 font-mono text-xs text-content-secondary">
                          {step.latitude.toFixed(6)}
                        </td>
                        <td className="px-5 py-3 font-mono text-xs text-content-secondary">
                          {step.longitude.toFixed(6)}
                        </td>
                        <td className="px-5 py-3 font-mono text-xs">
                          <VelocityIndicator velocity={step.velocity_kmh} />
                        </td>
                        <td className="px-5 py-3 text-xs text-content-tertiary">
                          {new Date(step.timestamp).toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-warning/6 border border-warning/15">
              <Navigation className="h-5 w-5 text-warning shrink-0" />
              <p className="text-sm text-warning font-medium">
                No path steps returned — the case may have insufficient data.
              </p>
            </div>
          )}
        </>
      )}
    </section>
  );
}

// ── Velocity Indicator ──────────────────────────────────────────────────

function VelocityIndicator({ velocity }: { velocity: number }) {
  return (
    <span className={cn('inline-flex items-center space-x-1.5', velocityColor(velocity))}>
      <Gauge className="w-3.5 h-3.5" />
      <span className="font-semibold">{velocity.toFixed(1)}</span>
      <span className="text-[10px] opacity-70 uppercase font-medium">
        {velocityLabel(velocity)}
      </span>
    </span>
  );
}

// ── Stat Tile ───────────────────────────────────────────────────────────

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
