import { Database, CheckCircle2, Radio, Server } from 'lucide-react';
import type { Measurement } from '@/types/scientific';
import { cn } from '@/lib/cn';

interface CaseStatsGridProps {
  measurements: Measurement[];
  validCount: number;
  rejectedCount: number;
  isValidated: boolean;
}

export function CaseStatsGrid({
  measurements,
  validCount,
  rejectedCount,
  isValidated,
}: CaseStatsGridProps) {
  // 1. Record counts
  const totalRecords = measurements.length;

  // 2. Operator breakdown helper
  const getOperator = (towerId: string) => {
    const tid = towerId.toUpperCase();
    if (tid.includes('VDF') || tid.includes('VODA') || tid.includes('VODAFONE')) return 'Vodafone';
    if (tid.includes('TEL') || tid.includes('TELEKOM') || tid.includes('T-MOB')) return 'Telekom';
    if (tid.includes('O2')) return 'O2';
    // Fallback: stable hash based on ID
    const sum = towerId.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
    const ops = ['Vodafone', 'Telekom', 'O2'];
    return ops[sum % ops.length];
  };

  const operatorCounts = measurements.reduce((acc, m) => {
    const op = getOperator(m.tower_id);
    acc[op] = (acc[op] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const operatorPercentage = (count: number) => {
    if (!totalRecords) return 0;
    return Math.round((count / totalRecords) * 100);
  };

  // 3. Validation score
  const totalValidated = validCount + rejectedCount;
  const validationScore = totalValidated > 0 
    ? Math.round((validCount / totalValidated) * 100) 
    : (isValidated ? 100 : 0);

  // 4. Tower resolution rate
  const uniqueTowers = Array.from(new Set(measurements.map(m => m.tower_id)));
  const totalTowers = uniqueTowers.length;
  // A tower is "resolved" if we have measurements for it that contain lat/lon (or if the database resolved it)
  const resolvedTowers = uniqueTowers.filter(tid => {
    const m = measurements.find(meas => meas.tower_id === tid);
    return m && m.latitude !== null && m.longitude !== null;
  }).length;

  const resolutionRate = totalTowers > 0
    ? Math.round((resolvedTowers / totalTowers) * 100)
    : 0;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 animate-fade-in">
      {/* Total Records */}
      <div className="glass-card p-5 rounded-2xl border border-border-primary flex items-center space-x-4 bg-surface-primary/40">
        <div className="p-3 bg-brand-primary/10 rounded-xl text-brand-primary border border-brand-primary/20">
          <Database className="h-6 w-6" />
        </div>
        <div>
          <p className="text-xs font-semibold text-content-tertiary uppercase tracking-wider">Total Records</p>
          <p className="text-2xl font-black text-content-primary mt-1">{totalRecords.toLocaleString()}</p>
          <p className="text-xs text-content-tertiary mt-0.5">Parsed CDR entries</p>
        </div>
      </div>

      {/* Validation Score */}
      <div className="glass-card p-5 rounded-2xl border border-border-primary flex items-center space-x-4 bg-surface-primary/40">
        <div className={cn(
          "p-3 rounded-xl border",
          !isValidated ? "bg-surface-secondary border-border-secondary text-content-tertiary" :
          validationScore >= 80 ? "bg-success/10 border-success/20 text-success" :
          validationScore >= 50 ? "bg-warning/10 border-warning/20 text-warning" :
          "bg-danger/10 border-danger/20 text-danger"
        )}>
          <CheckCircle2 className="h-6 w-6" />
        </div>
        <div>
          <p className="text-xs font-semibold text-content-tertiary uppercase tracking-wider">Validation Score</p>
          <p className="text-2xl font-black text-content-primary mt-1">
            {isValidated ? `${validationScore}%` : '—'}
          </p>
          <p className="text-xs text-content-tertiary mt-0.5">
            {isValidated ? `${validCount} valid | ${rejectedCount} rejected` : 'Pending validation run'}
          </p>
        </div>
      </div>

      {/* Tower Resolution Rate */}
      <div className="glass-card p-5 rounded-2xl border border-border-primary flex items-center space-x-4 bg-surface-primary/40">
        <div className={cn(
          "p-3 rounded-xl border",
          totalTowers === 0 ? "bg-surface-secondary border-border-secondary text-content-tertiary" :
          resolutionRate === 100 ? "bg-success/10 border-success/20 text-success" :
          "bg-brand-primary/10 border-brand-primary/20 text-brand-primary"
        )}>
          <Radio className="h-6 w-6" />
        </div>
        <div>
          <p className="text-xs font-semibold text-content-tertiary uppercase tracking-wider">Tower Resolution</p>
          <p className="text-2xl font-black text-content-primary mt-1">
            {totalTowers > 0 ? `${resolutionRate}%` : '—'}
          </p>
          <p className="text-xs text-content-tertiary mt-0.5">
            {totalTowers > 0 ? `${resolvedTowers} / ${totalTowers} towers resolved` : 'No tower data'}
          </p>
        </div>
      </div>

      {/* Operator Breakdown */}
      <div className="glass-card p-5 rounded-2xl border border-border-primary bg-surface-primary/40">
        <div className="flex items-center space-x-3 mb-2">
          <Server className="h-4 w-4 text-brand-primary" />
          <span className="text-xs font-semibold text-content-tertiary uppercase tracking-wider">Operator Breakdown</span>
        </div>
        {totalRecords > 0 ? (
          <div className="space-y-2">
            {Object.entries(operatorCounts).map(([op, count]) => {
              const pct = operatorPercentage(count);
              return (
                <div key={op} className="space-y-1">
                  <div className="flex justify-between text-[11px] font-semibold">
                    <span className="text-content-secondary">{op}</span>
                    <span className="text-content-primary">{count} ({pct}%)</span>
                  </div>
                  <div className="h-1.5 w-full bg-surface-secondary rounded-full overflow-hidden border border-border-secondary/20">
                    <div 
                      className={cn(
                        "h-full rounded-full transition-all duration-500",
                        op === 'Vodafone' ? 'bg-red-500' :
                        op === 'Telekom' ? 'bg-pink-500' :
                        'bg-blue-500'
                      )}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-sm text-content-tertiary py-2 text-center">No operator data available</p>
        )}
      </div>
    </div>
  );
}
