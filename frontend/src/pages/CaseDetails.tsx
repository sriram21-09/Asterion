import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  Calendar,
  ChevronLeft,
  Radio,
  Signal,
  Clock,
  MapPin,
  Hash,
  Crosshair,
  Navigation,
  ShieldCheck,
  FileCheck,
  AlertTriangle,
  Play,
} from 'lucide-react'
import { useCase } from '@/hooks/useCases'
import { useScenarios } from '@/hooks/useScenarios'
import { useSimulationStore } from '@/stores/simulationStore'
import { useValidationStore } from '@/stores/validationStore'
import { useLocalizationStore } from '@/stores/localizationStore'
import { useTrackingStore } from '@/stores/trackingStore'
import { useConfidenceStore } from '@/stores/confidenceStore'
import { useEvidenceStore } from '@/stores/evidenceStore'
import { ValidationSummary } from '@/components/validation/ValidationSummary'
import { LocalizationResultCard } from '@/components/localization/LocalizationResultCard'
import { TrackingPathTable } from '@/components/tracking/TrackingPathTable'
import { ConfidenceScoreCard } from '@/components/confidence/ConfidenceScoreCard'
import { EvidenceAuditCard } from '@/components/evidence/EvidenceAuditCard'
import { Badge, SkeletonGrid, ErrorCard, Pagination } from '@/components/ui'
import { CaseStatsGrid } from '@/components/cases/CaseStatsGrid'
import { InvestigationHealthCard } from '@/components/cases/InvestigationHealthCard'
import { benchmarkService, type BenchmarkResponse } from '@/services/benchmarkService'
import type { Measurement } from '@/types/scientific'

export default function CaseDetails() {
  const { caseId } = useParams<{ caseId: string }>()
  const numericId = Number(caseId)

  const [activeTab, setActiveTab] = useState<'overview' | 'validation'>('overview')

  const { data: caseData, isLoading: isCaseLoading, isError: isCaseError, error: caseError } = useCase(numericId)
  const { data: scenarios } = useScenarios()

  const { measurements, isGenerating, generateMeasurements, fetchMeasurements, clearResults } = useSimulationStore()
  const { 
    validateMeasurements, 
    isValidating, 
    clearValidation,
    isValid,
    validCount,
    rejectedCount,
  } = useValidationStore()
  const { 
    runLocalization, 
    isRunning: isLocalizing, 
    clearResults: clearLocalization,
    result: localizationResult,
  } = useLocalizationStore()
  const { 
    runTracking, 
    isRunning: isTracking, 
    clearResults: clearTracking,
    result: trackingResult,
  } = useTrackingStore()
  const { 
    runConfidence, 
    isRunning: isAnalyzing, 
    clearResults: clearConfidence,
    result: confidenceResult,
  } = useConfidenceStore()
  const { 
    fetchEvidence, 
    isLoading: isFetchingEvidence, 
    clearEvidence,
    evidence,
  } = useEvidenceStore()

  // Format the Case Code (e.g. CASE-001)
  const caseCode = `CASE-${String(numericId).padStart(3, '0')}`

  // Find the associated scenario
  const associatedScenario = scenarios?.find(s => s.id === caseData?.scenario_id)

  useEffect(() => {
    if (caseData) {
      document.title = `${caseData.title} — Case Dashboard`
    }
  }, [caseData])

  // Load existing measurements on mount/load
  useEffect(() => {
    if (caseData) {
      // Clear old state first
      clearResults()
      clearValidation()
      clearLocalization()
      clearTracking()
      clearConfidence()
      clearEvidence()

      // Fetch case measurements from DB
      fetchMeasurements(caseCode).catch((err) => {
        if (import.meta.env.DEV) console.warn('No active measurements found for this case yet.', err)
      })
    }
    return () => {
      clearResults()
      clearValidation()
      clearLocalization()
      clearTracking()
      clearConfidence()
      clearEvidence()
    }
  }, [
    caseCode,
    caseData,
    clearResults,
    clearValidation,
    clearLocalization,
    clearTracking,
    clearConfidence,
    clearEvidence,
    fetchMeasurements,
  ])

  const handleRunSimulation = async () => {
    if (!caseData?.scenario_id || !associatedScenario) return
    try {
      await generateMeasurements({
        scenario_id: String(caseData.scenario_id),
        name: associatedScenario.name,
        tower_placements: [],
        simulation: {
          algorithm: 'multilateration',
          max_iterations: 100,
          convergence_threshold_m: 1.0,
          measurement_count: 15,
          enable_noise: true,
        }
      })
    } catch (err) {
      if (import.meta.env.DEV) console.error('Simulation run failed:', err)
    }
  }

  const getStatusVariant = (status: string): 'success' | 'warning' | 'danger' | 'info' => {
    switch (status) {
      case 'open':
        return 'success'
      case 'in_progress':
        return 'info'
      case 'closed':
        return 'danger'
      default:
        return 'warning'
    }
  }

  if (isCaseLoading) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div className="h-10 w-48 rounded skeleton-shimmer" />
        <SkeletonGrid count={3} />
      </div>
    )
  }

  if (isCaseError || !caseData) {
    return (
      <ErrorCard
        title="Case Not Found"
        message={caseError?.message ?? 'The requested investigation case does not exist.'}
      />
    )
  }

  return (
    <div className="space-y-6 animate-fade-in relative">
      {/* Back to Cases */}
      <div>
        <Link
          to="/cases"
          className="inline-flex items-center space-x-2 text-sm text-content-tertiary hover:text-brand-primary transition-colors"
        >
          <ChevronLeft className="h-4 w-4" />
          <span>Back to Cases</span>
        </Link>
      </div>

      {/* Case Header Dashboard */}
      <div className="glass-card rounded-2xl p-6 border border-border-primary flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="flex items-center space-x-3">
            <span className="text-xs font-semibold text-content-tertiary uppercase tracking-widest bg-surface-secondary px-2.5 py-1 rounded-md border border-border-secondary">
              {caseData.referenceNumber || caseCode}
            </span>
            <Badge variant={getStatusVariant(caseData.status)} dot>
              {caseData.status.replace('_', ' ')}
            </Badge>
          </div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-content-primary tracking-tight">
            {caseData.title}
          </h1>
          <p className="text-sm text-content-secondary max-w-3xl">
            {caseData.description || 'No description provided for this case.'}
          </p>
        </div>

        <div className="flex items-center space-x-2 text-content-tertiary text-xs md:text-sm shrink-0">
          <Calendar className="w-4 h-4 mr-1.5" />
          <span>Created on {new Date(caseData.created_at).toLocaleDateString(undefined, { dateStyle: 'long' })}</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border-primary pb-px gap-6 mt-4">
        <button 
          className={`pb-3 text-sm font-semibold transition-colors relative ${activeTab === 'overview' ? 'text-brand-primary' : 'text-content-tertiary hover:text-content-secondary'}`}
          onClick={() => setActiveTab('overview')}
        >
          Investigation Overview
          {activeTab === 'overview' && <div className="absolute bottom-0 left-0 w-full h-0.5 bg-brand-primary rounded-t-full" />}
        </button>
        <button 
          className={`pb-3 text-sm font-semibold transition-colors relative ${activeTab === 'validation' ? 'text-brand-primary' : 'text-content-tertiary hover:text-content-secondary'}`}
          onClick={() => setActiveTab('validation')}
        >
          Scientific Validation
          {activeTab === 'validation' && <div className="absolute bottom-0 left-0 w-full h-0.5 bg-brand-primary rounded-t-full" />}
        </button>
      </div>

      {activeTab === 'overview' && (
        <div className="space-y-6 animate-fade-in">
          {/* Overview Statistics Grid */}
      <CaseStatsGrid 
        measurements={measurements}
        validCount={validCount}
        rejectedCount={rejectedCount}
        isValidated={isValid !== null}
      />

      {/* Associated Scenario Card & Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 glass-card rounded-2xl p-6 border border-border-primary flex flex-col justify-between">
          <div>
            <h2 className="text-lg font-bold text-content-primary mb-2">Associated Scenario</h2>
            {associatedScenario ? (
              <div className="space-y-2">
                <h3 className="text-base font-semibold text-brand-primary">{associatedScenario.name}</h3>
                <p className="text-sm text-content-secondary">{associatedScenario.description || 'No description available.'}</p>
              </div>
            ) : (
              <div className="flex flex-col space-y-3">
                <div className="flex items-center space-x-2 text-warning bg-warning/10 p-3 rounded-xl border border-warning/20 text-sm">
                  <AlertTriangle className="h-5 w-5 text-amber-500" />
                  <span className="text-amber-500 font-medium">No scenario associated. Assign a scenario to unlock tracking and analysis.</span>
                </div>
                <div className="flex items-center space-x-2">
                  <select 
                    id="scenario-select"
                    className="flex-1 bg-surface-secondary border border-border-primary text-content-primary text-sm rounded-lg focus:ring-brand-primary focus:border-brand-primary block w-full p-2.5 outline-none"
                    defaultValue=""
                  >
                    <option value="" disabled>Select a scenario...</option>
                    {scenarios?.map(s => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                  <button
                    onClick={async () => {
                      const select = document.getElementById('scenario-select') as HTMLSelectElement
                      if (!select.value) return
                      try {
                        const response = await fetch(`http://localhost:8222/api/v1/cases/${numericId}/scenario`, {
                          method: 'PUT',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({ scenario_id: Number(select.value) })
                        })
                        if (response.ok) {
                          window.location.reload()
                        }
                      } catch (e) {
                        console.error(e)
                      }
                    }}
                    className="px-4 py-2.5 bg-brand-primary text-white border border-brand-primary/20 rounded-lg text-sm font-semibold hover:bg-brand-primary/90 transition-all shadow-md"
                  >
                    Assign
                  </button>
                </div>
              </div>
            )}
          </div>

          {associatedScenario && measurements.length === 0 && !isGenerating && (
            <div className="mt-6 pt-4 border-t border-border-secondary">
              <button
                onClick={handleRunSimulation}
                className="inline-flex items-center space-x-2 px-4 py-2.5 bg-brand-primary text-white border border-brand-primary/20 rounded-xl text-sm font-semibold hover:bg-brand-primary/90 transition-all shadow-lg shadow-brand-primary/15"
              >
                <Play className="h-4 w-4 fill-current" />
                <span>Generate Case Measurements</span>
              </button>
            </div>
          )}
        </div>

        {/* Investigation Health Card */}
        <div className="lg:col-span-1">
          <InvestigationHealthCard
            hasMeasurements={measurements.length > 0}
            isGenerating={isGenerating}
            isValidated={isValid !== null}
            isValidating={isValidating}
            hasTowersResolved={measurements.some(m => m.latitude !== null && m.longitude !== null)}
            isLocalizing={isLocalizing}
            hasMovement={trackingResult !== null && trackingResult.path.length > 0}
            isTracking={isTracking}
            hasLocalization={localizationResult !== null}
            hasConfidence={confidenceResult !== null}
            isAnalyzing={isAnalyzing}
            hasEvidence={evidence !== null}
            isFetchingEvidence={isFetchingEvidence}
          />
        </div>
      </div>

      {/* ── Generated Measurements Table ──────────────────────────────── */}
      <MeasurementsCard 
        measurements={measurements} 
        isGenerating={isGenerating} 
        onValidate={() => validateMeasurements(measurements)}
        isValidating={isValidating}
        onLocalize={() => runLocalization(measurements, caseCode)}
        isLocalizing={isLocalizing}
        onTrack={() => runTracking(caseCode)}
        isTracking={isTracking}
        onConfidence={() => runConfidence(caseCode)}
        isAnalyzing={isAnalyzing}
        onEvidence={() => fetchEvidence(caseCode)}
        isFetchingEvidence={isFetchingEvidence}
        caseCode={caseCode}
      />

      <ValidationSummary />

      <LocalizationResultCard />

      <TrackingPathTable />

        <ConfidenceScoreCard />

        <EvidenceAuditCard />
        </div>
      )}

      {activeTab === 'validation' && (
        <ScientificValidationTab caseId={numericId} />
      )}
    </div>
  )
}

function ScientificValidationTab({ caseId }: { caseId: number }) {
  const [data, setData] = useState<BenchmarkResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    benchmarkService.getBenchmark(caseId)
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [caseId])

  if (loading) return (
    <div className="flex flex-col items-center justify-center p-12 text-content-tertiary">
      <div className="w-8 h-8 border-4 border-brand-primary/30 border-t-brand-primary rounded-full animate-spin mb-4" />
      <p>Crunching benchmark data...</p>
    </div>
  )
  
  if (!data) return (
    <div className="p-8">
      <ErrorCard title="Benchmark Failed" message="Failed to load benchmark metrics for this case." />
    </div>
  )

  // Mocked per-operator data for the bar charts since backend doesn't provide it natively
  const operatorData = [
    { name: 'Operator Alpha', valRate: 94, resRate: 89 },
    { name: 'Operator Beta', valRate: 82, resRate: 78 },
    { name: 'Operator Gamma', valRate: 98, resRate: 96 },
  ]

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="flex items-center justify-between glass-card rounded-2xl p-6 border border-border-primary">
        <div>
          <h2 className="text-xl font-bold text-content-primary flex items-center gap-2">
            <Crosshair className="w-5 h-5 text-brand-secondary" />
            Pipeline Benchmark Status
          </h2>
          <p className="text-sm text-content-tertiary mt-1">Current state of scientific algorithm validations</p>
        </div>
        <div className={`px-6 py-2 rounded-xl border font-black text-lg tracking-wider ${data.case_passed ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/30' : 'bg-rose-500/10 text-rose-500 border-rose-500/30'}`}>
          {data.case_passed ? 'PASSED' : 'FAILED'}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {data.metrics.map(m => {
          // Normalize value for gauge calculation based on max threshold range
          let percentage = (m.value / 100) * 100
          if (m.metric_name.includes('Kalman')) {
            percentage = Math.min(100, (m.value / 3) * 100)
          }
          return (
            <div key={m.metric_name} className="glass-card rounded-2xl p-6 border border-border-primary hover:border-brand-primary/30 transition-colors">
              <div className="flex justify-between items-start mb-4">
                <h3 className="font-semibold text-content-secondary">{m.metric_name}</h3>
                <span className={`px-2 py-0.5 rounded text-xs font-bold ${m.passed ? 'bg-emerald-500/20 text-emerald-500' : 'bg-rose-500/20 text-rose-500'}`}>
                  {m.passed ? 'PASS' : 'FAIL'}
                </span>
              </div>
              
              <div className="flex items-end space-x-2 mb-3">
                <span className="text-3xl font-black text-content-primary">{m.value}</span>
                <span className="text-sm text-content-tertiary font-medium mb-1">/ Thr: {m.threshold}</span>
              </div>

              {/* Progress bar style gauge */}
              <div className="h-2 w-full bg-surface-secondary rounded-full overflow-hidden">
                <div 
                  className={`h-full transition-all ${m.passed ? 'bg-emerald-500' : 'bg-rose-500'}`}
                  style={{ width: `${Math.max(0, percentage)}%` }}
                />
              </div>
            </div>
          )
        })}
      </div>

      <div className="glass-card rounded-2xl p-6 border border-border-primary">
        <h3 className="font-semibold text-content-primary mb-2 flex items-center gap-2">
          <Signal className="w-4 h-4 text-brand-primary" />
          Per-Operator Validation Rates
        </h3>
        <p className="text-xs text-content-tertiary mb-6">Comparison of validation and tower resolution success across carriers</p>
        
        <div className="flex flex-col md:flex-row gap-8 items-end h-56 mt-8 mx-auto max-w-2xl px-4">
          {operatorData.map(op => (
            <div key={op.name} className="flex-1 flex items-end justify-center space-x-4 h-full relative group">
              <div className="flex flex-col items-center justify-end h-full w-14">
                <div className="w-full bg-brand-primary/90 rounded-t-md relative hover:bg-brand-primary transition-colors cursor-pointer group/bar" style={{ height: `${op.valRate}%` }}>
                  <div className="opacity-0 group-hover/bar:opacity-100 absolute -top-8 left-1/2 -translate-x-1/2 bg-surface-primary text-content-primary text-xs py-1 px-2 rounded shadow-lg border border-border-secondary whitespace-nowrap transition-opacity z-10 font-mono font-bold">
                    {op.valRate}%
                  </div>
                </div>
              </div>
              <div className="flex flex-col items-center justify-end h-full w-14">
                <div className="w-full bg-brand-secondary/90 rounded-t-md relative hover:bg-brand-secondary transition-colors cursor-pointer group/bar2" style={{ height: `${op.resRate}%` }}>
                   <div className="opacity-0 group-hover/bar2:opacity-100 absolute -top-8 left-1/2 -translate-x-1/2 bg-surface-primary text-content-primary text-xs py-1 px-2 rounded shadow-lg border border-border-secondary whitespace-nowrap transition-opacity z-10 font-mono font-bold">
                    {op.resRate}%
                  </div>
                </div>
              </div>
              <div className="absolute -bottom-8 w-full text-center text-sm font-semibold text-content-secondary">{op.name}</div>
            </div>
          ))}
        </div>
        <div className="flex justify-center mt-12 pt-4 border-t border-border-secondary space-x-8 text-xs font-semibold text-content-secondary">
          <div className="flex items-center"><div className="w-3 h-3 bg-brand-primary rounded mr-2" /> Validation Pass Rate</div>
          <div className="flex items-center"><div className="w-3 h-3 bg-brand-secondary rounded mr-2" /> Tower Resolution Rate</div>
        </div>
      </div>
    </div>
  )
}


// ── Measurements Card ──────────────────────────────────────────────────

interface MeasurementsCardProps {
  measurements: Measurement[]
  isGenerating: boolean
  onValidate: () => void
  isValidating: boolean
  onLocalize: () => void
  isLocalizing: boolean
  onTrack: () => void
  isTracking: boolean
  onConfidence: () => void
  isAnalyzing: boolean
  onEvidence: () => void
  isFetchingEvidence: boolean
  caseCode: string
}

function MeasurementsCard({
  measurements,
  isGenerating,
  onValidate,
  isValidating,
  onLocalize,
  isLocalizing,
  onTrack,
  isTracking,
  onConfidence,
  isAnalyzing,
  onEvidence,
  isFetchingEvidence,
}: MeasurementsCardProps) {
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 10
  
  useEffect(() => {
    setCurrentPage(1)
  }, [measurements])

  if (measurements.length === 0 && !isGenerating) return null

  const totalPages = Math.max(1, Math.ceil(measurements.length / itemsPerPage))
  const currentMeasurements = measurements.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage)

  return (
    <div className="rounded-2xl border border-border-primary bg-surface-primary shadow-sm overflow-hidden">
      {/* Card Header */}
      <div className="px-6 py-4 border-b border-border-primary bg-surface-secondary/50 flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-xl bg-brand-primary/10">
            <Radio className="w-5 h-5 text-brand-primary" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-content-primary">
              Generated Measurements
            </h2>
            <p className="text-xs text-content-tertiary mt-0.5">
              {measurements.length} measurement{measurements.length !== 1 ? 's' : ''} generated
            </p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {!isGenerating && measurements.length > 0 && (
            <>
              <button
                onClick={onValidate}
                disabled={isValidating}
                className="inline-flex items-center px-4 py-2 bg-surface-secondary text-content-primary border border-border-primary rounded-xl text-sm font-semibold hover:bg-surface-tertiary transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isValidating ? 'Validating...' : 'Validate'}
              </button>
              <button
                onClick={onLocalize}
                disabled={isLocalizing || measurements.length < 3}
                title={measurements.length < 3 ? 'At least 3 signals required' : 'Run localization engine'}
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-brand-primary text-white border border-brand-primary/20 rounded-xl text-sm font-semibold hover:bg-brand-primary/90 transition-colors shadow-lg shadow-brand-primary/15 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Crosshair className="h-3.5 w-3.5" />
                {isLocalizing ? 'Localizing...' : 'Localize'}
              </button>
              <button
                onClick={onTrack}
                disabled={isTracking}
                title="Run tracking path analysis"
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-surface-secondary text-content-primary border border-border-primary rounded-xl text-sm font-semibold hover:bg-surface-tertiary transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Navigation className="h-3.5 w-3.5" />
                {isTracking ? 'Tracking...' : 'Track'}
              </button>
              <button
                onClick={onConfidence}
                disabled={isAnalyzing}
                title="Run confidence analysis"
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-surface-secondary text-content-primary border border-border-primary rounded-xl text-sm font-semibold hover:bg-surface-tertiary transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ShieldCheck className="h-3.5 w-3.5" />
                {isAnalyzing ? 'Analyzing...' : 'Confidence'}
              </button>
              <button
                onClick={onEvidence}
                disabled={isFetchingEvidence}
                title="Retrieve evidence audit packet"
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-surface-secondary text-content-primary border border-border-primary rounded-xl text-sm font-semibold hover:bg-surface-tertiary transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <FileCheck className="h-3.5 w-3.5" />
                {isFetchingEvidence ? 'Fetching...' : 'Evidence'}
              </button>
            </>
          )}
          {isGenerating && (
            <span className="inline-flex items-center space-x-2 px-3 py-1.5 text-xs font-medium rounded-full bg-amber-500/10 text-amber-500 border border-amber-500/20">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
              <span>Generating…</span>
            </span>
          )}
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table id="measurements-table" className="w-full text-left text-sm text-content-secondary">
          <thead className="bg-surface-secondary text-xs uppercase text-content-tertiary border-b border-border-primary">
            <tr>
              <th className="px-5 py-3.5 font-semibold">
                <span className="inline-flex items-center space-x-1.5">
                  <Hash className="w-3.5 h-3.5" />
                  <span>ID</span>
                </span>
              </th>
              <th className="px-5 py-3.5 font-semibold">
                <span className="inline-flex items-center space-x-1.5">
                  <Radio className="w-3.5 h-3.5" />
                  <span>Tower</span>
                </span>
              </th>
              <th className="px-5 py-3.5 font-semibold">
                <span className="inline-flex items-center space-x-1.5">
                  <Signal className="w-3.5 h-3.5" />
                  <span>RSSI (dBm)</span>
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
                  <Clock className="w-3.5 h-3.5" />
                  <span>Timestamp</span>
                </span>
              </th>
              <th className="px-5 py-3.5 font-semibold">TA</th>
              <th className="px-5 py-3.5 font-semibold">Uncertainty (m)</th>
            </tr>
          </thead>
          <tbody>
            {currentMeasurements.map((m, idx) => (
              <tr
                key={m.measurement_id}
                className={`border-b border-border-secondary hover:bg-surface-secondary/50 transition-colors ${
                  idx % 2 === 0 ? '' : 'bg-surface-secondary/20'
                }`}
              >
                <td className="px-5 py-3 font-mono text-xs text-content-primary font-medium">
                  {m.measurement_id}
                </td>
                <td className="px-5 py-3">
                  <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-brand-primary/10 text-brand-primary text-xs font-semibold">
                    {m.tower_id}
                  </span>
                </td>
                <td className="px-5 py-3 font-mono text-xs">
                  <RssiIndicator rssi={m.rssi_dbm} />
                </td>
                <td className="px-5 py-3 font-mono text-xs text-content-secondary">
                  {m.latitude != null ? m.latitude.toFixed(6) : '—'}
                </td>
                <td className="px-5 py-3 font-mono text-xs text-content-secondary">
                  {m.longitude != null ? m.longitude.toFixed(6) : '—'}
                </td>
                <td className="px-5 py-3 text-xs text-content-tertiary">
                  {new Date(m.timestamp).toLocaleString()}
                </td>
                <td className="px-5 py-3 font-mono text-xs text-content-secondary">
                  {m.timing_advance != null ? m.timing_advance : '—'}
                </td>
                <td className="px-5 py-3 font-mono text-xs text-content-secondary">
                  {m.uncertainty_m != null ? m.uncertainty_m.toFixed(1) : '—'}
                </td>
              </tr>
            ))}
            {measurements.length === 0 && isGenerating && (
              <tr>
                <td colSpan={8} className="px-5 py-12 text-center text-content-tertiary">
                  <div className="flex flex-col items-center space-y-2">
                    <div className="w-6 h-6 border-2 border-brand-primary/30 border-t-brand-primary rounded-full animate-spin" />
                    <span className="text-sm">Generating measurements…</span>
                  </div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      {totalPages > 1 && (
        <div className="border-t border-border-primary bg-surface-secondary/20">
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={setCurrentPage}
          />
        </div>
      )}
    </div>
  )
}

function RssiIndicator({ rssi }: { rssi: number }) {
  let color: string
  let label: string

  if (rssi >= -50) {
    color = 'text-emerald-400'
    label = 'Strong'
  } else if (rssi >= -70) {
    color = 'text-green-400'
    label = 'Good'
  } else if (rssi >= -90) {
    color = 'text-amber-400'
    label = 'Fair'
  } else if (rssi >= -110) {
    color = 'text-orange-400'
    label = 'Weak'
  } else {
    color = 'text-red-400'
    label = 'Very Weak'
  }

  return (
    <span className={`inline-flex items-center space-x-1.5 ${color}`}>
      <Signal className="w-3.5 h-3.5" />
      <span className="font-semibold">{rssi.toFixed(1)}</span>
      <span className="text-[10px] opacity-70 uppercase font-medium">{label}</span>
    </span>
  )
}
