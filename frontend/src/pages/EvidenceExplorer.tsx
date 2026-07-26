import { useState, useEffect } from 'react'
import { FileSearch, Hash, Cpu, CheckCircle2, XCircle, Clock, ShieldCheck, ChevronRight, Activity } from 'lucide-react'
import { cn } from '@/lib/cn'

interface EvidenceRun {
  id: string
  caseId: string
  timestamp: string
  solverVersion: string
  algorithmDetails: string
  reproducibilityHash: string
  status: 'Verified' | 'Pending' | 'Failed'
  description: string
  parameters: Record<string, string>
}

const MOCK_EVIDENCE_RUNS: EvidenceRun[] = [
  {
    id: 'EV-8472-A',
    caseId: 'CAS-2026-08',
    timestamp: '2026-07-25T14:30:00Z',
    solverVersion: 'v2.4.1-stable',
    algorithmDetails: 'Multilateration with Extended Kalman Filter',
    reproducibilityHash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    status: 'Verified',
    description: 'High confidence localization trace with dense urban propagation parameters.',
    parameters: {
      'Path Loss Exponent': '3.5',
      'Shadow Fading': '8.0 dB',
      'Iterations': '150',
      'Convergence': '0.5m',
    },
  },
  {
    id: 'EV-8473-B',
    caseId: 'CAS-2026-09',
    timestamp: '2026-07-24T09:15:00Z',
    solverVersion: 'v2.4.0-rc2',
    algorithmDetails: 'Weighted Centroid Approximation',
    reproducibilityHash: '8f434346648f6b96df89dda901c5176b10a6d83961dd3c1ac88b59b2dc327aa4',
    status: 'Pending',
    description: 'Sparse rural dataset pending secondary validation pass.',
    parameters: {
      'Path Loss Exponent': '2.2',
      'Shadow Fading': '4.0 dB',
      'Iterations': '50',
      'Convergence': '2.0m',
    },
  },
  {
    id: 'EV-8474-C',
    caseId: 'CAS-2026-10',
    timestamp: '2026-07-22T16:45:00Z',
    solverVersion: 'v2.3.8-legacy',
    algorithmDetails: 'Hybrid TDOA/RSS',
    reproducibilityHash: 'a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e',
    status: 'Failed',
    description: 'Convergence failed due to anomalous multipath interference.',
    parameters: {
      'Path Loss Exponent': '4.0',
      'Shadow Fading': '12.0 dB',
      'Iterations': '200',
      'Convergence': '0.1m',
    },
  },
]

export default function EvidenceExplorer() {
  const [selectedRun, setSelectedRun] = useState<EvidenceRun | null>(null)

  useEffect(() => {
    document.title = 'Evidence Explorer — Asterion'
    // Auto-select the first run
    if (MOCK_EVIDENCE_RUNS.length > 0) {
      setSelectedRun(MOCK_EVIDENCE_RUNS[0])
    }
  }, [])

  return (
    <div className="space-y-6 animate-fade-in pb-12 min-h-[calc(100vh-80px)] flex flex-col">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-border-primary pb-5 shrink-0">
        <div>
          <h1 className="text-3xl font-extrabold text-content-primary tracking-tight flex items-center space-x-3">
            <FileSearch className="h-8 w-8 text-brand-secondary" />
            <span>Evidence Explorer</span>
          </h1>
          <p className="text-sm text-content-tertiary mt-2">
            Audit logs, solver verification, and reproducibility hashes
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1 min-h-0">
        {/* Left Column: Evidence List */}
        <div className="lg:col-span-4 bg-surface-primary border border-border-primary rounded-2xl flex flex-col overflow-hidden">
          <div className="p-4 border-b border-border-primary bg-surface-secondary/50">
            <h2 className="text-lg font-bold text-content-primary flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-brand-primary" />
              Audit Trail
            </h2>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {MOCK_EVIDENCE_RUNS.map((run) => {
              const isSelected = selectedRun?.id === run.id
              return (
                <div
                  key={run.id}
                  onClick={() => setSelectedRun(run)}
                  className={cn(
                    'p-4 rounded-xl border transition-all cursor-pointer group',
                    isSelected
                      ? 'bg-brand-primary/10 border-brand-primary shadow-sm'
                      : 'bg-surface-secondary/30 border-border-secondary hover:border-brand-primary/40 hover:bg-surface-secondary',
                  )}
                >
                  <div className="flex justify-between items-start mb-2">
                    <h3 className={cn("font-bold text-sm", isSelected ? 'text-brand-primary' : 'text-content-primary')}>
                      {run.caseId}
                    </h3>
                    <StatusBadge status={run.status} />
                  </div>
                  <div className="text-xs text-content-tertiary font-mono mb-2 flex items-center gap-1.5">
                    <Clock className="w-3 h-3" />
                    {new Date(run.timestamp).toLocaleString()}
                  </div>
                  <div className="flex items-center justify-between mt-3 text-xs">
                    <span className="text-content-secondary flex items-center gap-1">
                      <Cpu className="w-3.5 h-3.5" />
                      {run.solverVersion}
                    </span>
                    <ChevronRight
                      className={cn(
                        'w-4 h-4 transition-transform',
                        isSelected ? 'text-brand-primary translate-x-1' : 'text-content-tertiary group-hover:translate-x-0.5'
                      )}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Right Column: Details Panel */}
        <div className="lg:col-span-8 bg-surface-primary border border-border-primary rounded-2xl flex flex-col overflow-hidden">
          {selectedRun ? (
            <>
              <div className="p-6 border-b border-border-primary bg-surface-secondary/50 flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <h2 className="text-2xl font-bold text-content-primary">
                      {selectedRun.id}
                    </h2>
                    <StatusBadge status={selectedRun.status} />
                  </div>
                  <p className="text-sm text-content-secondary">
                    Linked to Case: <span className="font-mono text-content-primary">{selectedRun.caseId}</span>
                  </p>
                </div>
                <div className="text-right">
                  <div className="text-xs text-content-tertiary mb-1">Execution Time</div>
                  <div className="text-sm font-medium text-content-primary font-mono">
                    {new Date(selectedRun.timestamp).toLocaleString()}
                  </div>
                </div>
              </div>

              <div className="flex-1 overflow-y-auto p-6 space-y-8">
                {/* Hash Panel */}
                <div className="space-y-3">
                  <h3 className="text-sm font-semibold text-content-tertiary uppercase tracking-wider flex items-center gap-2">
                    <Hash className="w-4 h-4" />
                    Reproducibility Hash (SHA-256)
                  </h3>
                  <div className="bg-surface-secondary border border-border-primary rounded-xl p-4 flex items-center gap-4">
                    <div className="w-10 h-10 rounded-full bg-brand-primary/10 flex items-center justify-center shrink-0 border border-brand-primary/20">
                      <ShieldCheck className="w-5 h-5 text-brand-primary" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-content-secondary mb-1">Cryptographic checksum for verification</p>
                      <code className="block text-xs font-mono text-brand-secondary bg-surface-primary px-3 py-2 rounded-lg border border-border-secondary truncate">
                        {selectedRun.reproducibilityHash}
                      </code>
                    </div>
                  </div>
                </div>

                {/* Solver & Algorithm Panel */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-3">
                    <h3 className="text-sm font-semibold text-content-tertiary uppercase tracking-wider flex items-center gap-2">
                      <Cpu className="w-4 h-4" />
                      Solver Details
                    </h3>
                    <div className="bg-surface-base border border-border-primary rounded-xl p-4 space-y-4">
                      <div>
                        <div className="text-xs text-content-tertiary mb-1">Solver Version</div>
                        <div className="text-sm font-medium text-content-primary font-mono">
                          {selectedRun.solverVersion}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-content-tertiary mb-1">Algorithm Strategy</div>
                        <div className="text-sm font-medium text-content-primary">
                          {selectedRun.algorithmDetails}
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <h3 className="text-sm font-semibold text-content-tertiary uppercase tracking-wider flex items-center gap-2">
                      <Activity className="w-4 h-4" />
                      Execution Parameters
                    </h3>
                    <div className="bg-surface-base border border-border-primary rounded-xl p-4">
                      <div className="space-y-3">
                        {Object.entries(selectedRun.parameters).map(([key, value]) => (
                          <div key={key} className="flex justify-between items-center text-sm border-b border-border-secondary pb-2 last:border-0 last:pb-0">
                            <span className="text-content-secondary">{key}</span>
                            <span className="font-mono text-content-primary font-medium">{value}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Description */}
                <div className="space-y-3">
                  <h3 className="text-sm font-semibold text-content-tertiary uppercase tracking-wider">
                    Execution Summary
                  </h3>
                  <div className="p-4 bg-surface-secondary rounded-xl border border-border-secondary text-sm text-content-secondary leading-relaxed">
                    {selectedRun.description}
                  </div>
                </div>

              </div>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-content-tertiary p-8">
              <FileSearch className="w-16 h-16 mb-4 opacity-20" />
              <p className="text-lg font-medium">No run selected</p>
              <p className="text-sm mt-1">Select an evidence run from the audit trail to view details.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function StatusBadge({ status }: { status: EvidenceRun['status'] }) {
  if (status === 'Verified') {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-bold rounded-md bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 uppercase tracking-wide">
        <CheckCircle2 className="w-3 h-3" /> {status}
      </span>
    )
  }
  if (status === 'Pending') {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-bold rounded-md bg-amber-500/10 text-amber-500 border border-amber-500/20 uppercase tracking-wide">
        <Clock className="w-3 h-3" /> {status}
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-bold rounded-md bg-red-500/10 text-red-500 border border-red-500/20 uppercase tracking-wide">
      <XCircle className="w-3 h-3" /> {status}
    </span>
  )
}
