import {
  FileCheck,
  Radio,
  CheckCircle,
  XCircle,
  AlertTriangle,
  MapPin,
  Hash,
} from 'lucide-react';
import { cn } from '@/lib/cn';
import { useEvidenceStore } from '@/stores/evidenceStore';
import { Badge } from '@/components/ui';

// ── Severity Config ─────────────────────────────────────────────────────

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

// ── Tower status helpers ────────────────────────────────────────────────

function towerStatusVariant(status: string): 'success' | 'warning' | 'danger' | 'info' {
  const s = status.toLowerCase();
  if (s === 'active' || s === 'used') return 'success';
  if (s === 'partial') return 'warning';
  if (s === 'rejected' || s === 'inactive') return 'danger';
  return 'info';
}

// ── Component ───────────────────────────────────────────────────────────

interface EvidenceAuditCardProps {
  className?: string;
}

/**
 * Glassmorphic evidence audit card.
 *
 * Displays:
 *   - Summary tiles: total measurements, accepted, rejected, towers total, towers used
 *   - Active towers table: tower_id, lat/lon, accepted/rejected counts, status
 *   - Rejected measurements with error checklists and severity badges
 *
 * Reads directly from `useEvidenceStore`.
 */
export function EvidenceAuditCard({ className }: EvidenceAuditCardProps) {
  const { evidence, isLoading, error } = useEvidenceStore();

  // ── Nothing to render ──────────────────────────────────────────────
  if (!evidence && !isLoading && !error) return null;

  const hasRejections = evidence ? evidence.rejections.length > 0 : false;

  return (
    <section
      id="evidence-audit-card"
      className={cn('glass-card rounded-2xl p-6 animate-fade-in', className)}
    >
      {/* ── Header ───────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-brand-primary/12 border border-brand-primary/20 flex items-center justify-center">
            <FileCheck className="h-5 w-5 text-brand-primary" />
          </div>
          <div>
            <h3 className="text-base font-bold text-content-primary">
              Evidence Audit
            </h3>
            <p className="text-xs text-content-tertiary mt-0.5">
              {isLoading
                ? 'Fetching audit evidence…'
                : evidence
                  ? `${evidence.case_code} — ${evidence.summary.accepted_measurements} accepted`
                  : 'Evidence retrieval failed'}
            </p>
          </div>
        </div>

        {/* Status badge */}
        {!isLoading && evidence && (
          <Badge
            variant={hasRejections ? 'warning' : 'success'}
            dot
          >
            {hasRejections
              ? `${evidence.summary.rejected_measurements} Rejected`
              : 'All Accepted'}
          </Badge>
        )}
      </div>

      {/* ── Shimmer while loading ──────────────────────────────────── */}
      {isLoading && (
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
      {!isLoading && error && (
        <div className="bg-danger/8 border border-danger/20 rounded-xl p-4 flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-danger shrink-0 mt-0.5" />
          <p className="text-sm text-danger leading-relaxed">{error}</p>
        </div>
      )}

      {/* ── Result content ─────────────────────────────────────────── */}
      {!isLoading && evidence && (
        <>
          {/* Summary stat tiles — 5 column */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 mb-5">
            <SummaryTile
              icon={<Hash className="h-4 w-4 text-brand-primary" />}
              label="Total"
              value={evidence.summary.total_measurements}
            />
            <SummaryTile
              icon={<CheckCircle className="h-4 w-4 text-success" />}
              label="Accepted"
              value={evidence.summary.accepted_measurements}
              highlight="success"
            />
            <SummaryTile
              icon={<XCircle className="h-4 w-4 text-danger" />}
              label="Rejected"
              value={evidence.summary.rejected_measurements}
              highlight={evidence.summary.rejected_measurements > 0 ? 'danger' : undefined}
            />
            <SummaryTile
              icon={<Radio className="h-4 w-4 text-info" />}
              label="Towers Total"
              value={evidence.summary.towers_total}
            />
            <SummaryTile
              icon={<Radio className="h-4 w-4 text-success" />}
              label="Towers Used"
              value={evidence.summary.towers_used_count}
            />
          </div>

          {/* ── Active Towers Table ───────────────────────────────────── */}
          {evidence.towers.length > 0 && (
            <div className="mb-5">
              <h4 className="text-xs font-semibold text-content-tertiary uppercase tracking-wider mb-2">
                Active Towers ({evidence.towers.length})
              </h4>
              <div className="rounded-xl border border-border-primary overflow-hidden">
                <div className="overflow-x-auto max-h-64 overflow-y-auto">
                  <table
                    id="evidence-towers-table"
                    className="w-full text-left text-sm text-content-secondary"
                  >
                    <thead className="bg-surface-secondary text-xs uppercase text-content-tertiary border-b border-border-primary sticky top-0 z-10">
                      <tr>
                        <th className="px-5 py-3 font-semibold">
                          <span className="inline-flex items-center space-x-1.5">
                            <Radio className="w-3.5 h-3.5" />
                            <span>Tower</span>
                          </span>
                        </th>
                        <th className="px-5 py-3 font-semibold">
                          <span className="inline-flex items-center space-x-1.5">
                            <MapPin className="w-3.5 h-3.5" />
                            <span>Lat / Lon</span>
                          </span>
                        </th>
                        <th className="px-5 py-3 font-semibold">Accepted</th>
                        <th className="px-5 py-3 font-semibold">Rejected</th>
                        <th className="px-5 py-3 font-semibold">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {evidence.towers.map((tower, idx) => (
                        <tr
                          key={tower.tower_id}
                          className={cn(
                            'border-b border-border-secondary hover:bg-surface-secondary/50 transition-colors',
                            idx % 2 !== 0 && 'bg-surface-secondary/20',
                          )}
                        >
                          <td className="px-5 py-3">
                            <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-brand-primary/10 text-brand-primary text-xs font-semibold">
                              {tower.tower_id}
                            </span>
                          </td>
                          <td className="px-5 py-3 font-mono text-xs text-content-secondary">
                            {tower.latitude.toFixed(6)}, {tower.longitude.toFixed(6)}
                          </td>
                          <td className="px-5 py-3 font-mono text-xs text-success font-medium">
                            {tower.accepted_measurements}
                          </td>
                          <td className="px-5 py-3 font-mono text-xs font-medium">
                            <span className={tower.rejected_measurements > 0 ? 'text-danger' : 'text-content-tertiary'}>
                              {tower.rejected_measurements}
                            </span>
                          </td>
                          <td className="px-5 py-3">
                            <Badge variant={towerStatusVariant(tower.status)} className="text-[10px]">
                              {tower.status}
                            </Badge>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* ── Rejection Error Checklist ─────────────────────────────── */}
          {evidence.rejections.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-content-tertiary uppercase tracking-wider mb-2">
                Rejections ({evidence.rejections.length})
              </h4>
              <div className="max-h-64 overflow-y-auto rounded-xl border border-border-primary divide-y divide-border-primary">
                {evidence.rejections.map((rejection, rIdx) => (
                  <div key={`rej-${rIdx}`} className="px-4 py-3">
                    {/* Rejection header */}
                    <div className="flex items-center gap-2 mb-2 flex-wrap">
                      <XCircle className="h-4 w-4 text-danger shrink-0" />
                      {rejection.measurement_id && (
                        <span className="text-xs font-mono font-semibold text-content-secondary">
                          {rejection.measurement_id}
                        </span>
                      )}
                      {rejection.tower_id && (
                        <Badge variant="info" className="text-[10px]">
                          {rejection.tower_id}
                        </Badge>
                      )}
                      {rejection.timestamp && (
                        <span className="text-[10px] text-content-tertiary">
                          {new Date(rejection.timestamp).toLocaleString()}
                        </span>
                      )}
                    </div>

                    {/* Error checklist */}
                    {rejection.errors.length > 0 && (
                      <div className="space-y-1 ml-6">
                        {rejection.errors.map((err, eIdx) => {
                          const cfg =
                            SEVERITY_CONFIG[err.severity as keyof typeof SEVERITY_CONFIG] ??
                            SEVERITY_CONFIG.error;
                          const Icon = cfg.icon;
                          return (
                            <div
                              key={`${rIdx}-${eIdx}`}
                              className={cn(
                                'flex items-start gap-2 px-3 py-2 rounded-lg',
                                cfg.rowClass,
                              )}
                            >
                              <Icon className={cn('h-3.5 w-3.5 shrink-0 mt-0.5', cfg.iconClass)} />
                              <div className="min-w-0 flex-1">
                                <div className="flex items-center gap-1.5 flex-wrap">
                                  <Badge variant={cfg.badgeVariant} className="text-[9px]">
                                    {cfg.label}
                                  </Badge>
                                  <span className="text-[10px] font-medium text-content-tertiary">
                                    {err.field}
                                  </span>
                                  <span className="text-[10px] font-mono text-content-tertiary">
                                    [{err.code}]
                                  </span>
                                </div>
                                <p className="text-xs text-content-secondary mt-0.5 leading-snug">
                                  {err.message}
                                </p>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* All-clear when no rejections */}
          {evidence.rejections.length === 0 && (
            <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-success/6 border border-success/15">
              <CheckCircle className="h-5 w-5 text-success shrink-0" />
              <p className="text-sm text-success font-medium">
                All {evidence.summary.accepted_measurements} measurement(s) accepted — no rejections found.
              </p>
            </div>
          )}
        </>
      )}
    </section>
  );
}

// ── Internal sub-component ──────────────────────────────────────────────

interface SummaryTileProps {
  icon: React.ReactNode;
  label: string;
  value: number;
  highlight?: 'success' | 'danger';
}

function SummaryTile({ icon, label, value, highlight }: SummaryTileProps) {
  return (
    <div
      className={cn(
        'rounded-xl border px-4 py-3 flex flex-col gap-1 transition-colors',
        highlight === 'danger'
          ? 'border-danger/20 bg-danger/5'
          : highlight === 'success'
            ? 'border-success/20 bg-success/5'
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
          highlight === 'danger'
            ? 'text-danger'
            : highlight === 'success'
              ? 'text-success'
              : 'text-content-primary',
        )}
      >
        {value}
      </span>
    </div>
  );
}
