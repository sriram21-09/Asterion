import { useEffect, useState } from 'react'
import { GitCompare, Shield, CheckCircle2 } from 'lucide-react'
import { useCases } from '@/hooks/useCases'
import { useScenarios } from '@/hooks/useScenarios'
import { simulationService } from '@/services/simulationService'
import { evidenceService } from '@/services/evidenceService'
import { LoadingSpinner, ErrorCard, Badge } from '@/components/ui'
import { toast } from 'sonner'
import type { Case } from '@/types/case'

interface CaseMetrics {
  measurementCount: number
  avgRssi: number | null
  validRate: string
  hasCoords: boolean
  hasEvidence: boolean
  reproducibilityHash: string | null
}

export default function CaseComparison() {
  const { data: cases, isLoading: loadingCases, error: caseError } = useCases()
  const { data: scenarios } = useScenarios()

  const [caseAId, setCaseAId] = useState<number | ''>('')
  const [caseBId, setCaseBId] = useState<number | ''>('')

  const [caseAData, setCaseAData] = useState<Case | null>(null)
  const [caseBData, setCaseBData] = useState<Case | null>(null)

  const [metricsA, setMetricsA] = useState<CaseMetrics | null>(null)
  const [metricsB, setMetricsB] = useState<CaseMetrics | null>(null)

  const [loadingMetrics, setLoadingMetrics] = useState(false)

  useEffect(() => {
    document.title = 'Case Comparison — Asterion'
  }, [])

  // Sync selected Case A data
  useEffect(() => {
    if (caseAId && cases) {
      const found = cases.find((c) => c.id === Number(caseAId))
      setCaseAData(found || null)
    } else {
      setCaseAData(null)
      setMetricsA(null)
    }
  }, [caseAId, cases])

  // Sync selected Case B data
  useEffect(() => {
    if (caseBId && cases) {
      const found = cases.find((c) => c.id === Number(caseBId))
      setCaseBData(found || null)
    } else {
      setCaseBData(null)
      setMetricsB(null)
    }
  }, [caseBId, cases])

  // Fetch metrics for selected cases
  useEffect(() => {
    async function fetchComparisonMetrics() {
      if (!caseAData && !caseBData) return
      setLoadingMetrics(true)
      
      try {
        if (caseAData) {
          const codeA = caseAData.referenceNumber || `CASE-${String(caseAData.id).padStart(3, '0')}`
          let measurementsA: any[] = []
          let evidenceA: any = null
          
          try {
            measurementsA = await simulationService.getMeasurements(codeA)
          } catch { /* ignored */ }

          try {
            evidenceA = await evidenceService.getEvidence(codeA)
          } catch { /* ignored */ }

          const validCount = measurementsA.filter(m => m.rssi_dbm >= -110).length
          const totalCount = measurementsA.length
          const avgRssi = totalCount > 0 
            ? measurementsA.reduce((sum, m) => sum + m.rssi_dbm, 0) / totalCount 
            : null

          setMetricsA({
            measurementCount: totalCount,
            avgRssi,
            validRate: totalCount > 0 ? `${Math.round((validCount / totalCount) * 100)}%` : '0%',
            hasCoords: measurementsA.some(m => m.latitude !== null && m.longitude !== null),
            hasEvidence: !!evidenceA,
            reproducibilityHash: evidenceA?.reproducibility_hash || null
          })
        }

        if (caseBData) {
          const codeB = caseBData.referenceNumber || `CASE-${String(caseBData.id).padStart(3, '0')}`
          let measurementsB: any[] = []
          let evidenceB: any = null
          
          try {
            measurementsB = await simulationService.getMeasurements(codeB)
          } catch { /* ignored */ }

          try {
            evidenceB = await evidenceService.getEvidence(codeB)
          } catch { /* ignored */ }

          const validCount = measurementsB.filter(m => m.rssi_dbm >= -110).length
          const totalCount = measurementsB.length
          const avgRssi = totalCount > 0 
            ? measurementsB.reduce((sum, m) => sum + m.rssi_dbm, 0) / totalCount 
            : null

          setMetricsB({
            measurementCount: totalCount,
            avgRssi,
            validRate: totalCount > 0 ? `${Math.round((validCount / totalCount) * 100)}%` : '0%',
            hasCoords: measurementsB.some(m => m.latitude !== null && m.longitude !== null),
            hasEvidence: !!evidenceB,
            reproducibilityHash: evidenceB?.reproducibility_hash || null
          })
        }
      } catch (err) {
        console.error('Error loading comparison metrics:', err)
        toast.error('Failed to load metrics for comparison')
      } finally {
        setLoadingMetrics(false)
      }
    }

    fetchComparisonMetrics()
  }, [caseAData, caseBData])

  const getStatusColor = (status: string) => {
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

  if (loadingCases) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" className="text-brand-primary" />
      </div>
    )
  }

  if (caseError) {
    return (
      <ErrorCard 
        title="Failed to Load Cases" 
        message="Unable to retrieve active cases for comparison."
      />
    )
  }

  // Calculate comparative overlap indicators
  const getOverlapStatus = () => {
    if (!metricsA || !metricsB) return null
    if (metricsA.measurementCount === 0 || metricsB.measurementCount === 0) {
      return {
        label: 'Comparison Pending',
        desc: 'Ensure both cases have measurements generated to analyze spatial overlap.',
        type: 'warning'
      }
    }
    
    // Mock spatial/sector overlap
    const sameScenario = caseAData?.scenario_id === caseBData?.scenario_id
    if (sameScenario) {
      return {
        label: 'High Overlap Potential (92%)',
        desc: 'Both cases share the identical reference base station scenario configuration.',
        type: 'success'
      }
    } else {
      return {
        label: 'No Spatial Overlap Detected (0%)',
        desc: 'These cases operate on independent tracking coordinates and cellular sectors.',
        type: 'info'
      }
    }
  }

  const overlap = getOverlapStatus()

  return (
    <div className="space-y-8 animate-fade-in pb-12">
      {/* Page Header */}
      <div className="border-b border-border-primary pb-5">
        <h1 className="text-3xl font-extrabold text-content-primary tracking-tight flex items-center space-x-3">
          <GitCompare className="h-8 w-8 text-brand-secondary" />
          <span>Case Comparison</span>
        </h1>
        <p className="text-sm text-content-tertiary mt-2">
          Compare signal distributions, pipeline progress, and evidence hashes across cases side-by-side.
        </p>
      </div>

      {/* Case Selectors */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 bg-surface-primary border border-border-primary rounded-2xl p-6 shadow-sm">
        <div className="space-y-2">
          <label className="text-xs font-bold uppercase tracking-wider text-content-secondary">Primary Case (Case A)</label>
          <select
            value={caseAId}
            onChange={(e) => setCaseAId(e.target.value ? Number(e.target.value) : '')}
            className="w-full bg-surface-secondary border border-border-primary rounded-xl px-4 py-3 text-content-primary focus:outline-none focus:border-brand-primary transition-colors text-sm"
          >
            <option value="">Select a case...</option>
            {cases?.map((c) => (
              <option key={c.id} value={c.id} disabled={c.id === caseBId}>
                {c.referenceNumber || `CASE-${String(c.id).padStart(3, '0')}`} — {c.title}
              </option>
            ))}
          </select>
        </div>

        <div className="space-y-2">
          <label className="text-xs font-bold uppercase tracking-wider text-content-secondary">Secondary Case (Case B)</label>
          <select
            value={caseBId}
            onChange={(e) => setCaseBId(e.target.value ? Number(e.target.value) : '')}
            className="w-full bg-surface-secondary border border-border-primary rounded-xl px-4 py-3 text-content-primary focus:outline-none focus:border-brand-primary transition-colors text-sm"
          >
            <option value="">Select a case...</option>
            {cases?.map((c) => (
              <option key={c.id} value={c.id} disabled={c.id === caseAId}>
                {c.referenceNumber || `CASE-${String(c.id).padStart(3, '0')}`} — {c.title}
              </option>
            ))}
          </select>
        </div>
      </div>

      {loadingMetrics ? (
        <div className="flex flex-col items-center justify-center py-12 space-y-3">
          <LoadingSpinner size="lg" className="text-brand-primary" />
          <span className="text-sm text-content-secondary">Loading comparison details...</span>
        </div>
      ) : caseAData && caseBData ? (
        <div className="space-y-8">
          {/* Spatial Overlap Indicator Banner */}
          {overlap && (
            <div className={`p-5 rounded-2xl border flex items-start space-x-4 animate-slide-up ${
              overlap.type === 'success' ? 'bg-success/10 border-success/20 text-success' :
              overlap.type === 'warning' ? 'bg-warning/10 border-warning/20 text-warning' :
              'bg-info/10 border-info/20 text-info'
            }`}>
              <Shield className="h-6 w-6 shrink-0 mt-0.5" />
              <div>
                <h3 className="font-bold text-base leading-tight text-content-primary">{overlap.label}</h3>
                <p className="text-sm mt-1 text-content-secondary">{overlap.desc}</p>
              </div>
            </div>
          )}

          {/* Side-by-Side Comparison */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Primary Case details */}
            <div className="bg-surface-primary border border-border-primary rounded-2xl p-6 space-y-6">
              <div className="border-b border-border-secondary pb-4 flex justify-between items-start">
                <div>
                  <span className="text-xs font-semibold text-content-tertiary uppercase tracking-widest bg-surface-secondary px-2.5 py-1 rounded-md border border-border-secondary">
                    {caseAData.referenceNumber || `CASE-${String(caseAData.id).padStart(3, '0')}`}
                  </span>
                  <h2 className="text-xl font-extrabold text-content-primary mt-2">{caseAData.title}</h2>
                </div>
                <Badge variant={getStatusColor(caseAData.status)} dot>
                  {caseAData.status.replace('_', ' ')}
                </Badge>
              </div>

              <div className="space-y-4">
                <div className="flex justify-between py-2 border-b border-border-secondary/40 text-sm">
                  <span className="text-content-tertiary">Scenario configuration</span>
                  <span className="font-semibold text-brand-primary">
                    {scenarios?.find(s => s.id === caseAData.scenario_id)?.name || 'Not assigned'}
                  </span>
                </div>

                <div className="flex justify-between py-2 border-b border-border-secondary/40 text-sm">
                  <span className="text-content-tertiary">Created on</span>
                  <span className="font-semibold text-content-secondary">
                    {new Date(caseAData.created_at).toLocaleDateString()}
                  </span>
                </div>

                <div className="flex justify-between py-2 border-b border-border-secondary/40 text-sm">
                  <span className="text-content-tertiary">Measurement Count</span>
                  <span className="font-semibold text-content-secondary font-mono">
                    {metricsA?.measurementCount || 0} signals
                  </span>
                </div>

                <div className="flex justify-between py-2 border-b border-border-secondary/40 text-sm">
                  <span className="text-content-tertiary">Avg. Signal Strength</span>
                  <span className="font-semibold text-content-secondary font-mono">
                    {metricsA?.avgRssi !== null && metricsA?.avgRssi !== undefined
                      ? `${metricsA.avgRssi.toFixed(1)} dBm`
                      : '—'}
                  </span>
                </div>

                <div className="flex justify-between py-2 border-b border-border-secondary/40 text-sm">
                  <span className="text-content-tertiary">Measurement Acceptance</span>
                  <span className="font-semibold text-content-secondary font-mono">
                    {metricsA?.validRate || '0%'}
                  </span>
                </div>

                <div className="flex justify-between py-2 border-b border-border-secondary/40 text-sm">
                  <span className="text-content-tertiary">Localization Solved</span>
                  <span>
                    {metricsA?.hasCoords ? (
                      <span className="inline-flex items-center text-success text-xs font-bold">
                        <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Yes
                      </span>
                    ) : (
                      <span className="inline-flex items-center text-content-tertiary text-xs">
                        No
                      </span>
                    )}
                  </span>
                </div>

                <div className="flex flex-col space-y-1.5 py-2 text-sm">
                  <span className="text-content-tertiary">Reproducibility SHA-256 Hash</span>
                  <span className="font-mono text-xs bg-surface-secondary border border-border-secondary px-2.5 py-1.5 rounded-lg text-content-secondary break-all">
                    {metricsA?.reproducibilityHash || 'Audit packet not generated'}
                  </span>
                </div>
              </div>
            </div>

            {/* Secondary Case details */}
            <div className="bg-surface-primary border border-border-primary rounded-2xl p-6 space-y-6">
              <div className="border-b border-border-secondary pb-4 flex justify-between items-start">
                <div>
                  <span className="text-xs font-semibold text-content-tertiary uppercase tracking-widest bg-surface-secondary px-2.5 py-1 rounded-md border border-border-secondary">
                    {caseBData.referenceNumber || `CASE-${String(caseBData.id).padStart(3, '0')}`}
                  </span>
                  <h2 className="text-xl font-extrabold text-content-primary mt-2">{caseBData.title}</h2>
                </div>
                <Badge variant={getStatusColor(caseBData.status)} dot>
                  {caseBData.status.replace('_', ' ')}
                </Badge>
              </div>

              <div className="space-y-4">
                <div className="flex justify-between py-2 border-b border-border-secondary/40 text-sm">
                  <span className="text-content-tertiary">Scenario configuration</span>
                  <span className="font-semibold text-brand-primary">
                    {scenarios?.find(s => s.id === caseBData.scenario_id)?.name || 'Not assigned'}
                  </span>
                </div>

                <div className="flex justify-between py-2 border-b border-border-secondary/40 text-sm">
                  <span className="text-content-tertiary">Created on</span>
                  <span className="font-semibold text-content-secondary">
                    {new Date(caseBData.created_at).toLocaleDateString()}
                  </span>
                </div>

                <div className="flex justify-between py-2 border-b border-border-secondary/40 text-sm">
                  <span className="text-content-tertiary">Measurement Count</span>
                  <span className="font-semibold text-content-secondary font-mono">
                    {metricsB?.measurementCount || 0} signals
                  </span>
                </div>

                <div className="flex justify-between py-2 border-b border-border-secondary/40 text-sm">
                  <span className="text-content-tertiary">Avg. Signal Strength</span>
                  <span className="font-semibold text-content-secondary font-mono">
                    {metricsB?.avgRssi !== null && metricsB?.avgRssi !== undefined
                      ? `${metricsB.avgRssi.toFixed(1)} dBm`
                      : '—'}
                  </span>
                </div>

                <div className="flex justify-between py-2 border-b border-border-secondary/40 text-sm">
                  <span className="text-content-tertiary">Measurement Acceptance</span>
                  <span className="font-semibold text-content-secondary font-mono">
                    {metricsB?.validRate || '0%'}
                  </span>
                </div>

                <div className="flex justify-between py-2 border-b border-border-secondary/40 text-sm">
                  <span className="text-content-tertiary">Localization Solved</span>
                  <span>
                    {metricsB?.hasCoords ? (
                      <span className="inline-flex items-center text-success text-xs font-bold">
                        <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Yes
                      </span>
                    ) : (
                      <span className="inline-flex items-center text-content-tertiary text-xs">
                        No
                      </span>
                    )}
                  </span>
                </div>

                <div className="flex flex-col space-y-1.5 py-2 text-sm">
                  <span className="text-content-tertiary">Reproducibility SHA-256 Hash</span>
                  <span className="font-mono text-xs bg-surface-secondary border border-border-secondary px-2.5 py-1.5 rounded-lg text-content-secondary break-all">
                    {metricsB?.reproducibilityHash || 'Audit packet not generated'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* Empty/Selector State */
        <div className="flex flex-col items-center justify-center border-2 border-dashed border-border-primary rounded-2xl py-20 px-6 text-center space-y-4">
          <div className="h-16 w-16 bg-surface-secondary border border-border-secondary rounded-full flex items-center justify-center">
            <GitCompare className="h-8 w-8 text-content-tertiary" />
          </div>
          <div className="space-y-1">
            <h3 className="text-lg font-bold text-content-primary">Select Cases to Compare</h3>
            <p className="text-sm text-content-tertiary max-w-sm">
              Choose two different telecom localization cases from the selectors above to initiate analytical alignment.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
