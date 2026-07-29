import { useEffect, useState } from 'react'
import { GitCompare, Shield, CheckCircle2, BarChart3, Layers, Signal, Hash, Target, TrendingUp, AlertCircle } from 'lucide-react'
import { useCases } from '@/hooks/useCases'
import { useScenarios } from '@/hooks/useScenarios'
import { comparisonService, type ComparisonResult } from '@/services/comparisonService'
import { LoadingSpinner, ErrorCard, Badge } from '@/components/ui'
import { toast } from 'sonner'

// ── Pure CSS Bar Chart Component ─────────────────────────────────────────
function ComparisonBar({ label, valueA, valueB, maxVal, unit, colorA = '#3b82f6', colorB = '#8b5cf6' }: {
  label: string; valueA: number; valueB: number; maxVal: number; unit?: string; colorA?: string; colorB?: string
}) {
  const pctA = maxVal > 0 ? Math.min((valueA / maxVal) * 100, 100) : 0
  const pctB = maxVal > 0 ? Math.min((valueB / maxVal) * 100, 100) : 0
  return (
    <div className="space-y-2">
      <div className="flex justify-between text-xs font-semibold text-content-secondary">
        <span>{label}</span>
        <span className="font-mono text-content-tertiary">{unit || ''}</span>
      </div>
      <div className="space-y-1.5">
        <div className="flex items-center gap-3">
          <span className="text-[10px] font-bold w-8 text-right" style={{ color: colorA }}>A</span>
          <div className="flex-1 h-5 bg-surface-secondary rounded-full overflow-hidden border border-border-secondary">
            <div className="h-full rounded-full transition-all duration-700 ease-out flex items-center justify-end pr-2"
              style={{ width: `${Math.max(pctA, 2)}%`, background: `linear-gradient(90deg, ${colorA}33, ${colorA})` }}>
              <span className="text-[10px] font-bold text-white drop-shadow-sm">{valueA.toFixed(1)}</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-[10px] font-bold w-8 text-right" style={{ color: colorB }}>B</span>
          <div className="flex-1 h-5 bg-surface-secondary rounded-full overflow-hidden border border-border-secondary">
            <div className="h-full rounded-full transition-all duration-700 ease-out flex items-center justify-end pr-2"
              style={{ width: `${Math.max(pctB, 2)}%`, background: `linear-gradient(90deg, ${colorB}33, ${colorB})` }}>
              <span className="text-[10px] font-bold text-white drop-shadow-sm">{valueB.toFixed(1)}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Radial/Donut Chart Component ─────────────────────────────────────────
function RadialChart({ value, max, label, color = '#3b82f6', size = 100 }: {
  value: number; max: number; label: string; color?: string; size?: number
}) {
  const pct = max > 0 ? Math.min(value / max, 1) : 0
  const r = (size - 12) / 2
  const circ = 2 * Math.PI * r
  const offset = circ * (1 - pct)
  return (
    <div className="flex flex-col items-center gap-2">
      <svg width={size} height={size} className="transform -rotate-90">
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="currentColor" strokeWidth="6"
          className="text-surface-secondary" />
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth="6"
          strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round"
          className="transition-all duration-1000 ease-out" />
      </svg>
      <div className="text-center -mt-[calc(50%+8px)] mb-4">
        <span className="text-lg font-extrabold text-content-primary">{Math.round(pct * 100)}%</span>
      </div>
      <span className="text-[10px] font-semibold text-content-tertiary uppercase tracking-wider">{label}</span>
    </div>
  )
}

// ── Metric Card ──────────────────────────────────────────────────────────
function MetricCard({ icon: Icon, label, valueA, valueB, suffix }: {
  icon: any; label: string; valueA: string | number; valueB: string | number; suffix?: string
}) {
  return (
    <div className="bg-surface-primary border border-border-secondary rounded-xl p-4 space-y-3">
      <div className="flex items-center gap-2 text-xs font-semibold text-content-tertiary uppercase tracking-wider">
        <Icon className="w-3.5 h-3.5" /> {label}
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className="text-center p-2 bg-blue-500/5 border border-blue-500/10 rounded-lg">
          <div className="text-lg font-extrabold text-blue-500">{valueA}{suffix}</div>
          <div className="text-[10px] font-bold text-blue-400/70 uppercase">Case A</div>
        </div>
        <div className="text-center p-2 bg-purple-500/5 border border-purple-500/10 rounded-lg">
          <div className="text-lg font-extrabold text-purple-500">{valueB}{suffix}</div>
          <div className="text-[10px] font-bold text-purple-400/70 uppercase">Case B</div>
        </div>
      </div>
    </div>
  )
}

export default function CaseComparison() {
  const { data: cases, isLoading: loadingCases, error: caseError } = useCases()
  const { data: scenarios } = useScenarios()

  const [caseAId, setCaseAId] = useState<number | ''>('')
  const [caseBId, setCaseBId] = useState<number | ''>('')
  const [comparison, setComparison] = useState<ComparisonResult | null>(null)
  const [loadingMetrics, setLoadingMetrics] = useState(false)
  const [compError, setCompError] = useState<string | null>(null)

  useEffect(() => { document.title = 'Case Comparison — Asterion' }, [])

  // Run comparison when both cases are selected
  useEffect(() => {
    if (!caseAId || !caseBId || caseAId === caseBId) {
      setComparison(null)
      return
    }
    runComparison(Number(caseAId), Number(caseBId))
  }, [caseAId, caseBId])

  const runComparison = async (idA: number, idB: number) => {
    setLoadingMetrics(true)
    setCompError(null)
    try {
      const result = await comparisonService.compareCase(idA, idB)
      setComparison(result)
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Comparison failed'
      setCompError(msg)
      toast.error(msg)
    } finally {
      setLoadingMetrics(false)
    }
  }

  const caseAData = cases?.find(c => c.id === Number(caseAId)) || null
  const caseBData = cases?.find(c => c.id === Number(caseBId)) || null

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'open': return 'success'
      case 'in_progress': return 'info'
      case 'closed': return 'danger'
      default: return 'warning'
    }
  }

  if (loadingCases) {
    return <div className="flex items-center justify-center h-64"><LoadingSpinner size="lg" className="text-brand-primary" /></div>
  }
  if (caseError) {
    return <ErrorCard title="Failed to Load Cases" message="Unable to retrieve active cases for comparison." />
  }

  const mA = comparison?.metricsA
  const mB = comparison?.metricsB

  // Compute maxes for bar chart scaling
  const maxMeasurements = Math.max(mA?.measurementCount || 1, mB?.measurementCount || 1)
  const maxTowers = Math.max(mA?.towerCount || 1, mB?.towerCount || 1)
  const absMaxRssi = Math.max(Math.abs(mA?.avgRssi || 80), Math.abs(mB?.avgRssi || 80))

  return (
    <div className="space-y-8 animate-fade-in pb-12">
      {/* Header */}
      <div className="border-b border-border-primary pb-5">
        <h1 className="text-3xl font-extrabold text-content-primary tracking-tight flex items-center space-x-3">
          <GitCompare className="h-8 w-8 text-brand-secondary" />
          <span>Case Comparison</span>
        </h1>
        <p className="text-sm text-content-tertiary mt-2">
          Compare signal distributions, tower overlap, and confidence metrics across cases side-by-side.
        </p>
      </div>

      {/* Case Selectors */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 bg-surface-primary border border-border-primary rounded-2xl p-6 shadow-sm">
        <div className="space-y-2">
          <label className="text-xs font-bold uppercase tracking-wider text-content-secondary flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-blue-500" /> Primary Case (A)
          </label>
          <select value={caseAId} onChange={(e) => setCaseAId(e.target.value ? Number(e.target.value) : '')}
            className="w-full bg-surface-secondary border border-border-primary rounded-xl px-4 py-3 text-content-primary focus:outline-none focus:border-brand-primary transition-colors text-sm">
            <option value="">Select a case...</option>
            {cases?.map(c => (
              <option key={c.id} value={c.id} disabled={c.id === caseBId}>
                {c.referenceNumber || `CASE-${String(c.id).padStart(3, '0')}`} — {c.title}
              </option>
            ))}
          </select>
        </div>
        <div className="space-y-2">
          <label className="text-xs font-bold uppercase tracking-wider text-content-secondary flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-purple-500" /> Secondary Case (B)
          </label>
          <select value={caseBId} onChange={(e) => setCaseBId(e.target.value ? Number(e.target.value) : '')}
            className="w-full bg-surface-secondary border border-border-primary rounded-xl px-4 py-3 text-content-primary focus:outline-none focus:border-brand-primary transition-colors text-sm">
            <option value="">Select a case...</option>
            {cases?.map(c => (
              <option key={c.id} value={c.id} disabled={c.id === caseAId}>
                {c.referenceNumber || `CASE-${String(c.id).padStart(3, '0')}`} — {c.title}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Error state */}
      {compError && <ErrorCard title="Comparison Failed" message={compError} onRetry={() => caseAId && caseBId && runComparison(Number(caseAId), Number(caseBId))} />}

      {/* Loading state */}
      {loadingMetrics && (
        <div className="flex flex-col items-center justify-center py-16 space-y-3">
          <LoadingSpinner size="lg" className="text-brand-primary" />
          <span className="text-sm text-content-secondary">Analyzing cases and computing overlap...</span>
        </div>
      )}

      {/* Results */}
      {comparison && caseAData && caseBData && !loadingMetrics && (
        <div className="space-y-8">
          {/* Overlap Banner */}
          <div className={`p-5 rounded-2xl border flex items-start space-x-4 animate-slide-up ${
            comparison.overlapPercentage > 50 ? 'bg-success/10 border-success/20' :
            comparison.overlapPercentage > 0 ? 'bg-warning/10 border-warning/20' :
            'bg-info/10 border-info/20'
          }`}>
            <Shield className="h-6 w-6 shrink-0 mt-0.5 text-content-primary" />
            <div>
              <h3 className="font-bold text-base text-content-primary">
                Tower Overlap: {comparison.overlapPercentage}% ({comparison.overlappingTowerCount} shared towers)
              </h3>
              <p className="text-sm mt-1 text-content-secondary">
                Case A has {comparison.uniqueTowersA} unique tower(s), Case B has {comparison.uniqueTowersB} unique tower(s).
                {comparison.overlappingTowerCount > 0 && ` Shared: ${comparison.overlappingTowerIds.join(', ')}`}
              </p>
            </div>
          </div>

          {/* Visual Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Radial Charts */}
            <div className="bg-surface-primary border border-border-primary rounded-2xl p-6">
              <h3 className="text-sm font-bold text-content-primary mb-6 flex items-center gap-2">
                <Target className="w-4 h-4 text-brand-primary" /> Acceptance & Overlap
              </h3>
              <div className="flex justify-around">
                <RadialChart value={mA?.validRate || 0} max={100} label="Case A Valid" color="#3b82f6" />
                <RadialChart value={comparison.overlapPercentage} max={100} label="Tower Overlap" color="#10b981" />
                <RadialChart value={mB?.validRate || 0} max={100} label="Case B Valid" color="#8b5cf6" />
              </div>
            </div>

            {/* Bar Charts */}
            <div className="lg:col-span-2 bg-surface-primary border border-border-primary rounded-2xl p-6">
              <h3 className="text-sm font-bold text-content-primary mb-6 flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-brand-primary" /> Comparative Metrics
              </h3>
              <div className="space-y-5">
                <ComparisonBar label="Measurements" valueA={mA?.measurementCount || 0} valueB={mB?.measurementCount || 0} maxVal={maxMeasurements} unit="signals" />
                <ComparisonBar label="Tower Count" valueA={mA?.towerCount || 0} valueB={mB?.towerCount || 0} maxVal={maxTowers} unit="towers" />
                <ComparisonBar label="Avg. Signal Strength" valueA={Math.abs(mA?.avgRssi || 0)} valueB={Math.abs(mB?.avgRssi || 0)} maxVal={absMaxRssi} unit="dBm (abs)" />
                <ComparisonBar label="Avg. Uncertainty" valueA={mA?.avgUncertainty || 0} valueB={mB?.avgUncertainty || 0} maxVal={Math.max(mA?.avgUncertainty || 1, mB?.avgUncertainty || 1)} unit="meters" />
              </div>
            </div>
          </div>

          {/* Metric Cards Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricCard icon={Signal} label="Measurements" valueA={mA?.measurementCount || 0} valueB={mB?.measurementCount || 0} />
            <MetricCard icon={Layers} label="Towers" valueA={mA?.towerCount || 0} valueB={mB?.towerCount || 0} />
            <MetricCard icon={TrendingUp} label="Signal Strength" valueA={mA?.avgRssi?.toFixed(1) || '—'} valueB={mB?.avgRssi?.toFixed(1) || '—'} suffix=" dBm" />
            <MetricCard icon={Target} label="Acceptance" valueA={mA?.validRate || 0} valueB={mB?.validRate || 0} suffix="%" />
          </div>

          {/* Side-by-Side Case Cards */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {[{ data: caseAData, metrics: mA, color: 'blue' }, { data: caseBData, metrics: mB, color: 'purple' }].map(({ data, metrics, color }, idx) => (
              <div key={idx} className="bg-surface-primary border border-border-primary rounded-2xl p-6 space-y-5">
                <div className="border-b border-border-secondary pb-4 flex justify-between items-start">
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <div className={`w-3 h-3 rounded-full bg-${color}-500`} />
                      <span className="text-xs font-semibold text-content-tertiary uppercase tracking-widest bg-surface-secondary px-2.5 py-1 rounded-md border border-border-secondary">
                        {data.referenceNumber || `CASE-${String(data.id).padStart(3, '0')}`}
                      </span>
                    </div>
                    <h2 className="text-xl font-extrabold text-content-primary">{data.title}</h2>
                  </div>
                  <Badge variant={getStatusColor(data.status)} dot>{data.status.replace('_', ' ')}</Badge>
                </div>

                <div className="space-y-3">
                  {[
                    ['Scenario', scenarios?.find(s => s.id === data.scenario_id)?.name || 'Not assigned'],
                    ['Created', new Date(data.created_at).toLocaleDateString()],
                    ['Measurements', `${metrics?.measurementCount || 0} signals`],
                    ['Avg. Signal', metrics?.avgRssi != null ? `${metrics.avgRssi.toFixed(1)} dBm` : '—'],
                    ['Signal Range', metrics?.minRssi != null ? `${metrics.minRssi} to ${metrics.maxRssi} dBm` : '—'],
                    ['Acceptance Rate', `${metrics?.validRate || 0}%`],
                  ].map(([k, v]) => (
                    <div key={k} className="flex justify-between py-2 border-b border-border-secondary/40 text-sm">
                      <span className="text-content-tertiary">{k}</span>
                      <span className="font-semibold text-content-secondary">{v}</span>
                    </div>
                  ))}

                  <div className="flex justify-between py-2 border-b border-border-secondary/40 text-sm">
                    <span className="text-content-tertiary">Localization Solved</span>
                    <span>{metrics?.hasCoords
                      ? <span className="inline-flex items-center text-success text-xs font-bold"><CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Yes</span>
                      : <span className="inline-flex items-center text-content-tertiary text-xs"><AlertCircle className="w-3.5 h-3.5 mr-1" /> No</span>}
                    </span>
                  </div>

                  <div className="flex flex-col space-y-1.5 py-2 text-sm">
                    <span className="text-content-tertiary flex items-center gap-1.5"><Hash className="w-3 h-3" /> Reproducibility SHA-256</span>
                    <span className="font-mono text-xs bg-surface-secondary border border-border-secondary px-2.5 py-1.5 rounded-lg text-content-secondary break-all">
                      {metrics?.reproducibilityHash || 'Audit packet not generated'}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!comparison && !loadingMetrics && !compError && (
        <div className="flex flex-col items-center justify-center border-2 border-dashed border-border-primary rounded-2xl py-20 px-6 text-center space-y-4">
          <div className="h-16 w-16 bg-surface-secondary border border-border-secondary rounded-full flex items-center justify-center">
            <GitCompare className="h-8 w-8 text-content-tertiary" />
          </div>
          <div className="space-y-1">
            <h3 className="text-lg font-bold text-content-primary">Select Cases to Compare</h3>
            <p className="text-sm text-content-tertiary max-w-sm">
              Choose two different cases from the selectors above to analyze tower overlap, signal distributions, and evidence integrity.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
