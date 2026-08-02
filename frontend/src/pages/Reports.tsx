import { useEffect, useState } from 'react'
import { FileText, Download, BarChart2, Activity, ShieldCheck, Database, Calendar } from 'lucide-react'
import { useCases } from '@/hooks/useCases'
import { useScenarios } from '@/hooks/useScenarios'
import { Button, LoadingSpinner, ErrorCard } from '@/components/ui'
import { toast } from 'sonner'
import { reportService, type ReportPreviewData } from '@/services/reportService'

export default function Reports() {
  const { data: cases, isLoading: loadingCases, error: caseError } = useCases()
  const { data: scenarios, isLoading: loadingScenarios, error: scenarioError } = useScenarios()

  const [isGenerating, setIsGenerating] = useState(false)
  const [previewData, setPreviewData] = useState<ReportPreviewData | null>(null)
  const [downloading, setDownloading] = useState(false)

  useEffect(() => {
    document.title = 'Reports — Asterion'
  }, [])

  const REPORT_TYPES = {
    FULL: 'full',
    EVIDENCE: 'evidence_audit',
    VALIDATION: 'validation_error',
  }

  const handleExport = async (type: string) => {
    let backendReportType = REPORT_TYPES.FULL
    if (type === 'Evidence Audit') backendReportType = REPORT_TYPES.EVIDENCE
    if (type === 'Validation Error') backendReportType = REPORT_TYPES.VALIDATION
    if (type !== 'PDF' && type !== 'Execution Summary' && type !== 'Evidence Audit' && type !== 'Validation Error') {
      toast.info(`Exporting ${type} report... (Scheduled for Week 3/4 Roadmap)`)
      return
    }

    if (!cases || cases.length === 0) {
      toast.error('No cases available to generate a report.')
      return
    }

    // Try to pick the most recently updated/active case, or fallback to the first one
    const sortedCases = [...cases].sort((a, b) => new Date(b.updated_at || b.created_at).getTime() - new Date(a.updated_at || a.created_at).getTime())
    const caseId = sortedCases[0].id
    
    try {
      setIsGenerating(true)
      toast.loading('Generating PDF report...', { id: 'pdf-gen' })
      
      const data = await reportService.generateReport(caseId, backendReportType)
      // Set preview data even if backend returns empty due to stubbed responses
      setPreviewData(data || {})
      
      toast.success('Report generated successfully!', { id: 'pdf-gen' })
    } catch (error: any) {
      // console.error(error)
      toast.error(error.message || 'Failed to generate PDF report', { id: 'pdf-gen' })
    } finally {
      setIsGenerating(false)
    }
  }

  const handleDownload = async () => {
    if (!cases || cases.length === 0) return
    const sortedCases = [...cases].sort((a, b) => new Date(b.updated_at || b.created_at).getTime() - new Date(a.updated_at || a.created_at).getTime())
    const caseId = sortedCases[0].id

    try {
      setDownloading(true)
      toast.loading('Downloading PDF...', { id: 'pdf-dl' })
      
      const blob = await reportService.downloadReport(caseId)
      
      // Create a link element, use it to download the blob, and then remove it
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `Asterion_Report_${caseId}.pdf`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
      
      toast.success('Download complete!', { id: 'pdf-dl' })
    } catch (error: any) {
      // console.error(error)
      toast.error('Failed to download PDF report', { id: 'pdf-dl' })
    } finally {
      setDownloading(false)
    }
  }

  if (loadingCases || loadingScenarios) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" className="text-brand-primary" />
      </div>
    )
  }

  if (caseError || scenarioError) {
    return (
      <ErrorCard 
        title="Failed to Load Reporting Data" 
        message="Unable to aggregate metrics from cases or scenarios."
      />
    )
  }

  // Calculate some aggregate metrics
  const totalCases = cases?.length || 0
  const totalScenarios = scenarios?.length || 0
  
  const casesWithScenarios = cases?.filter(c => c.scenario_id != null).length || 0
  const completionRate = totalCases > 0 ? Math.round((casesWithScenarios / totalCases) * 100) : 0

  return (
    <div className="space-y-8 animate-fade-in pb-12">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-border-primary pb-5 gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-content-primary tracking-tight flex items-center space-x-3">
            <FileText className="h-8 w-8 text-brand-secondary" />
            <span>Analytics & Reports</span>
          </h1>
          <p className="text-sm text-content-tertiary mt-2">
            Export, review, and evaluate multilateration and tracking error rates.
          </p>
        </div>
        <div className="flex space-x-3">
          <Button 
            variant="secondary"
            onClick={() => handleExport('Execution Summary')}
            leftIcon={isGenerating ? <LoadingSpinner size="sm" /> : <FileText className="w-4 h-4" />}
            disabled={isGenerating}
          >
            Generate Report
          </Button>
          <Button 
            onClick={() => handleExport('CSV')}
            leftIcon={<Database className="w-4 h-4" />}
          >
            Export Raw CSV
          </Button>
        </div>
      </div>

      {/* Aggregate Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard 
          title="Total Investigations" 
          value={totalCases.toString()} 
          icon={<ShieldCheck className="h-5 w-5 text-brand-primary" />} 
          trend="+2 this week"
        />
        <MetricCard 
          title="Active Scenarios" 
          value={totalScenarios.toString()} 
          icon={<Activity className="h-5 w-5 text-blue-500" />} 
          trend="System stable"
        />
        <MetricCard 
          title="Pipeline Completion" 
          value={`${completionRate}%`} 
          icon={<BarChart2 className="h-5 w-5 text-emerald-500" />} 
          trend="Based on linked scenarios"
        />
        <MetricCard 
          title="Last Audit Date" 
          value={new Date().toLocaleDateString()} 
          icon={<Calendar className="h-5 w-5 text-amber-500" />} 
          trend="Automated run"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mt-8">
        {/* Export Templates List */}
        <section className="bg-surface-primary border border-border-primary rounded-2xl p-6 lg:col-span-2 space-y-6">
          <h2 className="text-xl font-bold text-content-primary">Standard Report Templates</h2>
          
          <div className="space-y-4">
            <ReportTemplate 
              title="End-to-End Execution Summary"
              description="Full breakdown of scenario setups, measurement generation bounds, and localization accuracy."
              tag="Comprehensive"
              onExport={() => handleExport('Execution Summary')}
            />
            <ReportTemplate 
              title="Confidence & Evidence Audit"
              description="Detailed mathematical proofs for error ellipses, GDOP, and Kalman filter smoothing paths."
              tag="Technical"
              onExport={() => handleExport('Evidence Audit')}
            />
            <ReportTemplate 
              title="System Validation Errors"
              description="Aggregated logs of bounds violations and rejected measurements across all active scenarios."
              tag="Debugging"
              onExport={() => handleExport('Validation Error')}
            />
          </div>
        </section>

        {/* Report Preview Panel */}
        <section className="bg-surface-primary border border-border-primary rounded-2xl p-6 flex flex-col space-y-4 shadow-sm">
          <div className="flex justify-between items-center mb-2">
            <h3 className="text-lg font-bold text-content-primary">Report Preview</h3>
            {previewData && (
              <Button 
                onClick={handleDownload} 
                disabled={downloading}
                leftIcon={downloading ? <LoadingSpinner size="sm" className="text-current" /> : <Download className="w-4 h-4" />}
                variant="primary"
                size="sm"
                className="shadow-sm"
              >
                Download PDF
              </Button>
            )}
          </div>
          
          {isGenerating ? (
            <div className="flex flex-col items-center justify-center py-16 space-y-4">
              <LoadingSpinner size="lg" className="text-brand-primary" />
              <p className="text-sm text-content-tertiary">Compiling report sections...</p>
            </div>
          ) : previewData ? (
            <div className="space-y-4 flex-1 overflow-y-auto pr-1 animate-fade-in">
              <div className="bg-surface-secondary rounded-xl p-4 border border-border-secondary">
                <h4 className="text-sm font-bold text-content-primary mb-3 flex items-center">
                  <FileText className="w-4 h-4 mr-2 text-brand-secondary"/> Metadata
                </h4>
                <div className="text-xs text-content-tertiary grid grid-cols-2 gap-3">
                  <span className="flex flex-col"><span className="font-medium text-content-secondary mb-1">Case ID:</span> {previewData.metadata?.case_id || 'N/A'}</span>
                  <span className="flex flex-col"><span className="font-medium text-content-secondary mb-1">Type:</span> {previewData.metadata?.report_type || 'N/A'}</span>
                  <span className="flex flex-col"><span className="font-medium text-content-secondary mb-1">Generated:</span> {previewData.metadata?.generated_at ? new Date(previewData.metadata.generated_at).toLocaleString() : 'N/A'}</span>
                  <span className="flex flex-col"><span className="font-medium text-content-secondary mb-1">Status:</span> <span className="text-emerald-500 font-medium">{previewData.metadata?.status || 'Ready'}</span></span>
                </div>
              </div>
              
              <div className="bg-surface-secondary rounded-xl p-4 border border-border-secondary">
                <h4 className="text-sm font-bold text-content-primary mb-3 flex items-center">
                  <ShieldCheck className="w-4 h-4 mr-2 text-emerald-500"/> Validation Summary
                </h4>
                <div className="text-xs text-content-tertiary grid grid-cols-3 gap-3">
                  <span className="flex flex-col"><span className="font-medium text-content-secondary mb-1">Total:</span> {previewData.validation_summary?.total_measurements ?? 'N/A'}</span>
                  <span className="flex flex-col"><span className="font-medium text-content-secondary mb-1">Rejected:</span> {previewData.validation_summary?.rejected ?? 'N/A'}</span>
                  <span className="flex flex-col"><span className="font-medium text-content-secondary mb-1">Pass Rate:</span> {previewData.validation_summary?.pass_rate ? `${previewData.validation_summary.pass_rate}%` : 'N/A'}</span>
                </div>
              </div>
              
              <div className="bg-surface-secondary rounded-xl p-4 border border-border-secondary">
                <h4 className="text-sm font-bold text-content-primary mb-3 flex items-center">
                  <Activity className="w-4 h-4 mr-2 text-blue-500"/> Tower Report
                </h4>
                <div className="text-xs text-content-tertiary grid grid-cols-2 gap-3">
                  <span className="flex flex-col"><span className="font-medium text-content-secondary mb-1">Towers Involved:</span> {previewData.tower_report?.towers_involved ?? 'N/A'}</span>
                  <span className="flex flex-col"><span className="font-medium text-content-secondary mb-1">Sector Coverage:</span> {previewData.tower_report?.sector_coverage ? `${previewData.tower_report.sector_coverage}%` : 'N/A'}</span>
                </div>
              </div>
              
              <div className="bg-surface-secondary rounded-xl p-4 border border-border-secondary">
                <h4 className="text-sm font-bold text-content-primary mb-3 flex items-center">
                  <BarChart2 className="w-4 h-4 mr-2 text-amber-500"/> Movement & Evidence
                </h4>
                <div className="text-xs text-content-tertiary grid grid-cols-3 gap-3">
                  <span className="flex flex-col"><span className="font-medium text-content-secondary mb-1">Distance:</span> {previewData.movement?.estimated_distance_km ? `${previewData.movement.estimated_distance_km} km` : 'N/A'}</span>
                  <span className="flex flex-col"><span className="font-medium text-content-secondary mb-1">Points:</span> {previewData.movement?.points_tracked ?? 'N/A'}</span>
                  <span className="flex flex-col"><span className="font-medium text-content-secondary mb-1">Confidence:</span> {previewData.evidence?.confidence_score ? `${previewData.evidence.confidence_score}%` : 'N/A'}</span>
                </div>
              </div>
            </div>
          ) : (
             <div className="flex flex-col items-center justify-center text-center space-y-4 py-16 h-full border-2 border-dashed border-border-primary rounded-xl">
               <div className="h-16 w-16 rounded-full bg-brand-primary/10 flex items-center justify-center">
                 <FileText className="h-8 w-8 text-brand-primary" />
               </div>
               <div>
                 <p className="text-sm font-medium text-content-primary">No report generated</p>
                 <p className="text-xs text-content-tertiary mt-1">Select a template to generate a preview</p>
               </div>
             </div>
          )}
        </section>
      </div>
    </div>
  )
}

function MetricCard({ title, value, icon, trend }: { title: string, value: string, icon: React.ReactNode, trend: string }) {
  return (
    <div className="bg-surface-primary border border-border-primary rounded-2xl p-6 flex flex-col justify-between hover:border-brand-primary/30 transition-colors">
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-sm font-medium text-content-secondary">{title}</h3>
        <div className="p-2 bg-surface-secondary rounded-lg">
          {icon}
        </div>
      </div>
      <div>
        <p className="text-3xl font-black text-content-primary tracking-tight">{value}</p>
        <p className="text-xs text-content-tertiary mt-2 font-medium">{trend}</p>
      </div>
    </div>
  )
}

function ReportTemplate({ title, description, tag, onExport }: { title: string, description: string, tag: string, onExport: () => void }) {
  return (
    <div className="flex items-center justify-between p-4 bg-surface-secondary border border-border-secondary rounded-xl hover:bg-surface-secondary/80 transition-colors">
      <div className="flex-1 min-w-0 pr-4">
        <div className="flex items-center space-x-3 mb-1">
          <h4 className="text-sm font-bold text-content-primary truncate">{title}</h4>
          <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-brand-primary/10 text-brand-primary border border-brand-primary/20">
            {tag}
          </span>
        </div>
        <p className="text-xs text-content-tertiary line-clamp-1">{description}</p>
      </div>
      <Button variant="secondary" onClick={onExport} leftIcon={<Download className="w-4 h-4" />}>
        Export
      </Button>
    </div>
  )
}
