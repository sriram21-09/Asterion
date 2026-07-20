import { useEffect } from 'react'
import { FileText, Download, BarChart2, Activity, ShieldCheck, Database, Calendar } from 'lucide-react'
import { useCases } from '@/hooks/useCases'
import { useScenarios } from '@/hooks/useScenarios'
import { Button, LoadingSpinner, ErrorCard } from '@/components/ui'
import { toast } from 'sonner'

export default function Reports() {
  const { data: cases, isLoading: loadingCases, error: caseError } = useCases()
  const { data: scenarios, isLoading: loadingScenarios, error: scenarioError } = useScenarios()

  useEffect(() => {
    document.title = 'Reports — Asterion'
  }, [])

  const handleExport = (type: string) => {
    toast.info(`Exporting ${type} report... (Mock action)`)
    setTimeout(() => toast.success(`${type} exported successfully.`), 1500)
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
  
  // Calculate how many cases have scenarios linked (roughly estimating "active" status for this mock report)
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
            onClick={() => handleExport('PDF')}
          >
            <Download className="w-4 h-4 mr-2 inline" />
            Export PDF
          </Button>
          <Button 
            onClick={() => handleExport('CSV')}
          >
            <Database className="w-4 h-4 mr-2 inline" />
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

        {/* Visual Analytics Placeholder */}
        <section className="bg-surface-primary border border-border-primary rounded-2xl p-6 flex flex-col justify-center items-center text-center space-y-4">
          <div className="h-24 w-24 rounded-full bg-brand-primary/10 flex items-center justify-center">
            <BarChart2 className="h-12 w-12 text-brand-primary" />
          </div>
          <h3 className="text-lg font-bold text-content-primary">Visual Analytics</h3>
          <p className="text-sm text-content-tertiary">
            Interactive error mapping and variance charts are currently in development for the next module update.
          </p>
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
      <Button variant="secondary" onClick={onExport}>
        <Download className="w-4 h-4 mr-2 inline" />
        Export
      </Button>
    </div>
  )
}
