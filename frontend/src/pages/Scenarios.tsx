import { useEffect, useState } from 'react'
import { Plus, LayoutGrid, List, Radio, Signal, Clock, MapPin, Hash, Crosshair, Navigation, ShieldCheck, FileCheck } from 'lucide-react'
import { useScenarios, useCreateScenario, useDeleteScenario } from '@/hooks/useScenarios'
import { ScenarioTable } from '@/components/scenarios/ScenarioTable'
import { ScenarioCard } from '@/components/scenarios/ScenarioCard'
import { ScenarioForm } from '@/components/scenarios/ScenarioForm'
import { EmptyState } from '@/components/scenarios/EmptyState'
import { SkeletonGrid, ErrorCard, ConfirmDialog } from '@/components/ui'
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
import type { CreateScenarioDTO } from '@/types/scenario'
import type { Measurement } from '@/types/scientific'

export default function Scenarios() {
  const [isFormOpen, setIsFormOpen] = useState(false)
  const [viewMode, setViewMode] = useState<'list' | 'grid'>('list')
  const [deleteTarget, setDeleteTarget] = useState<number | null>(null)

  const { data: scenarios, isLoading, isError, error, refetch } = useScenarios()
  const createScenario = useCreateScenario()
  const deleteScenario = useDeleteScenario()

  const { measurements, isGenerating, generateMeasurements } = useSimulationStore()
  const { validateMeasurements, isValidating } = useValidationStore()
  const { runLocalization, isRunning: isLocalizing } = useLocalizationStore()
  const { runTracking, isRunning: isTracking } = useTrackingStore()
  const { runConfidence, isRunning: isAnalyzing } = useConfidenceStore()
  const { fetchEvidence, isLoading: isFetchingEvidence } = useEvidenceStore()

  useEffect(() => {
    document.title = 'Scenarios — Asterion'
  }, [])

  const handleRunSimulation = async (id: number, name: string) => {
    try {
      await generateMeasurements({
        scenario_id: String(id),
        name: name,
        tower_placements: [],
        simulation: {
          algorithm: 'multilateration',
          max_iterations: 100,
          convergence_threshold_m: 1.0,
          measurement_count: 5,
          enable_noise: true,
        }
      })
    } catch (err) {
      console.error("Simulation run failed:", err)
    }
  }

  const handleCreateScenario = (data: CreateScenarioDTO) => {
    createScenario.mutate(data, {
      onSuccess: () => setIsFormOpen(false),
    })
  }

  const handleDeleteConfirm = () => {
    if (deleteTarget === null) return
    deleteScenario.mutate(deleteTarget, {
      onSettled: () => setDeleteTarget(null),
    })
  }

  return (
    <div className="space-y-6 animate-fade-in relative">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-border-primary pb-5">
        <div>
          <h1 className="text-3xl font-extrabold text-content-primary tracking-tight">
            Scenarios Configurator
          </h1>
          <p className="text-sm text-content-tertiary mt-1">
            Configure layout, transmitters, bounds, and signal paths.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          {scenarios && scenarios.length > 0 && (
            <div className="flex bg-surface-secondary border border-border-secondary rounded-lg p-1">
              <button
                onClick={() => setViewMode('list')}
                className={`p-1.5 rounded-md transition-all ${
                  viewMode === 'list'
                    ? 'bg-surface-primary shadow text-brand-primary'
                    : 'text-content-tertiary hover:text-content-secondary'
                }`}
                title="List View"
              >
                <List className="w-4 h-4" />
              </button>
              <button
                onClick={() => setViewMode('grid')}
                className={`p-1.5 rounded-md transition-all ${
                  viewMode === 'grid'
                    ? 'bg-surface-primary shadow text-brand-primary'
                    : 'text-content-tertiary hover:text-content-secondary'
                }`}
                title="Grid View"
              >
                <LayoutGrid className="w-4 h-4" />
              </button>
            </div>
          )}

          <button
            onClick={() => setIsFormOpen(true)}
            className="inline-flex items-center space-x-2 px-4 py-2.5 bg-brand-primary text-white border border-brand-primary/20 rounded-xl text-sm font-semibold hover:bg-brand-primary/90 transition-all shadow-lg shadow-brand-primary/15"
          >
            <Plus className="h-4 w-4" />
            <span>Add Scenario</span>
          </button>
        </div>
      </div>

      {/* Content Area */}
      {isLoading ? (
        <SkeletonGrid count={6} />
      ) : isError ? (
        <ErrorCard
          title="Error loading scenarios"
          message={error?.message ?? 'Please check your backend connection.'}
          onRetry={() => refetch()}
        />
      ) : !scenarios || scenarios.length === 0 ? (
        <EmptyState onCreateClick={() => setIsFormOpen(true)} />
      ) : (
        <>
          {viewMode === 'list' ? (
            <ScenarioTable
              scenarios={scenarios}
              onDelete={(id) => setDeleteTarget(id)}
              isDeleting={deleteScenario.isPending}
              onRunSimulation={(id, name) => handleRunSimulation(id, name)}
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {scenarios.map((s) => (
                <ScenarioCard
                  key={s.id}
                  scenarioData={s}
                  onDelete={(id) => setDeleteTarget(id)}
                  isDeleting={deleteScenario.isPending}
                />
              ))}
            </div>
          )}
        </>
      )}

      {/* ── Generated Measurements Table ──────────────────────────────── */}
      <MeasurementsCard 
        measurements={measurements} 
        isGenerating={isGenerating} 
        onValidate={() => validateMeasurements(measurements)}
        isValidating={isValidating}
        onLocalize={() => runLocalization(measurements)}
        isLocalizing={isLocalizing}
        onTrack={(caseCode) => runTracking(caseCode)}
        isTracking={isTracking}
        onConfidence={(caseCode) => runConfidence(caseCode)}
        isAnalyzing={isAnalyzing}
        onEvidence={(caseCode) => fetchEvidence(caseCode)}
        isFetchingEvidence={isFetchingEvidence}
      />

      <ValidationSummary />

      <LocalizationResultCard />

      <TrackingPathTable />

      <ConfidenceScoreCard />

      <EvidenceAuditCard />

      {/* Create Scenario Modal */}
      {isFormOpen && (
        <ScenarioForm
          onSubmit={handleCreateScenario}
          onCancel={() => setIsFormOpen(false)}
          isSubmitting={createScenario.isPending}
        />
      )}

      {/* Delete Confirmation Dialog */}
      {deleteTarget !== null && (
        <ConfirmDialog
          title="Delete Scenario"
          message="This action is permanent and cannot be undone. All transmitter and signal configurations in this scenario will be removed."
          confirmLabel="Delete Scenario"
          isDangerous
          isLoading={deleteScenario.isPending}
          onConfirm={handleDeleteConfirm}
          onCancel={() => setDeleteTarget(null)}
        />
      )}
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
  onTrack: (caseCode: string) => void
  isTracking: boolean
  onConfidence: (caseCode: string) => void
  isAnalyzing: boolean
  onEvidence: (caseCode: string) => void
  isFetchingEvidence: boolean
}

/**
 * Static table card displaying generated simulation measurements.
 * Visible once measurements have been generated via the simulation store.
 */
function MeasurementsCard({ measurements, isGenerating, onValidate, isValidating, onLocalize, isLocalizing, onTrack, isTracking, onConfidence, isAnalyzing, onEvidence, isFetchingEvidence }: MeasurementsCardProps) {
  if (measurements.length === 0 && !isGenerating) return null

  return (
    <div className="rounded-2xl border border-border-primary bg-surface-primary shadow-sm overflow-hidden">
      {/* Card Header */}
      <div className="px-6 py-4 border-b border-border-primary bg-surface-secondary/50 flex items-center justify-between">
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
        <div className="flex items-center space-x-3">
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
                onClick={() => onTrack('CASE-001')}
                disabled={isTracking}
                title="Run tracking path analysis"
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-surface-secondary text-content-primary border border-border-primary rounded-xl text-sm font-semibold hover:bg-surface-tertiary transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Navigation className="h-3.5 w-3.5" />
                {isTracking ? 'Tracking...' : 'Track'}
              </button>
              <button
                onClick={() => onConfidence('CASE-001')}
                disabled={isAnalyzing}
                title="Run confidence analysis"
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-surface-secondary text-content-primary border border-border-primary rounded-xl text-sm font-semibold hover:bg-surface-tertiary transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ShieldCheck className="h-3.5 w-3.5" />
                {isAnalyzing ? 'Analyzing...' : 'Confidence'}
              </button>
              <button
                onClick={() => onEvidence('CASE-001')}
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

// ── RSSI Strength Indicator ─────────────────────────────────────────────

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
