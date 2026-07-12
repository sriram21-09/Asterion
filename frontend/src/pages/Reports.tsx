import { useEffect } from 'react'
import { FileText } from 'lucide-react'

export default function Reports() {
  useEffect(() => {
    document.title = 'Reports — Asterion'
  }, [])

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="border-b border-border-primary pb-5">
        <h1 className="text-3xl font-extrabold text-content-primary tracking-tight">
          Analytics & Reports
        </h1>
        <p className="text-sm text-content-tertiary mt-1">
          Export, review, and evaluate multilateration and tracking error rates.
        </p>
      </div>

      <div className="bg-surface-primary border border-border-primary rounded-2xl p-12 text-center max-w-2xl mx-auto my-12 space-y-4">
        <div className="h-16 w-16 bg-surface-secondary border border-border-secondary rounded-2xl flex items-center justify-center mx-auto">
          <FileText className="h-8 w-8 text-brand-secondary" />
        </div>
        <div className="space-y-2">
          <h3 className="text-xl font-bold text-content-secondary">
            No reports generated
          </h3>
          <p className="text-sm text-content-tertiary max-w-sm mx-auto leading-relaxed">
            Report compilation engines, export formats, and mathematical
            analytics summaries will be configured in subsequent sprints.
          </p>
        </div>
      </div>
    </div>
  )
}
