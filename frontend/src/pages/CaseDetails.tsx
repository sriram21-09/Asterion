import { useEffect } from 'react'
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
import { Badge, SkeletonGrid, ErrorCard } from '@/components/ui'
import type { Measurement } from '@/types/scientific'

export default function CaseDetails() {
  const { caseId } = useParams<{ caseId: string }>()
  const numericId = Number(caseId)

  const { data: caseData, isLoading: isCaseLoading, isError: isCaseError, error: caseError } = useCase(numericId)
  const { data: scenarios } = useScenarios()

  const { measurements, isGenerating, generateMeasurements, fetchMeasurements, clearResults } = useSimulationStore()
  const { validateMeasurements, isValidating, clearValidation } = useValidationStore()
  const { runLocalization, isRunning: isLocalizing, clearResults: clearLocalization } = useLocalizationStore()
  const { runTracking, isRunning: isTracking, clearResults: clearTracking } = useTrackingStore()
  const { runConfidence, isRunning: isAnalyzing, clearResults: clearConfidence } = useConfidenceStore()
  const { fetchEvidence, isLoading: isFetchingEvidence, clearEvidence } = useEvidenceStore()

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
              <div className="flex items-center space-x-2 text-danger bg-danger/10 p-3 rounded-xl border border-danger/20 text-sm">
                <AlertTriangle className="h-5 w-5" />
                <span>No scenario associated. Assign a scenario to run localization.</span>
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

        {/* Quick Stats Panel */}
        <div className="glass-card rounded-2xl p-6 border border-border-primary flex flex-col justify-between">
          <div>
            <h2 className="text-lg font-bold text-content-primary mb-4">Pipeline Status</h2>
            <div className="space-y-3">
              <div className="flex justify-between items-center text-sm">
                <span className="text-content-secondary">Measurements</span>
                <span className="font-semibold text-content-primary">{measurements.length}</span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-content-secondary">Towers Detected</span>
                <span className="font-semibold text-content-primary">
                  {new Set(measurements.map(m => m.tower_id)).size}
                </span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-content-secondary">Engine Status</span>
                <span className={`font-semibold ${measurements.length > 0 ? 'text-success' : 'text-content-tertiary'}`}>
                  {measurements.length > 0 ? 'Ready' : 'Pending Simulation'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Generated Measurements Table ──────────────────────────────── */}
      <MeasurementsCard 
        measurements={measurements} 
        isGenerating={isGenerating} 
        onValidate={() => validateMeasurements(measurements)}
        isValidating={isValidating}
        onLocalize={() => runLocalization(measurements)}
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
  if (measurements.length === 0 && !isGenerating) return null

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
            {measurements.map((m, idx) => (
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
