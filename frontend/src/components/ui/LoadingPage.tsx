import { Radio } from 'lucide-react'
import { LoadingSpinner } from './LoadingSpinner'

interface LoadingPageProps {
  label?: string
}

/**
 * Full-screen centered loading view.
 * Use for route-level suspense, auth guards, or initial app load.
 */
export function LoadingPage({ label = 'Loading Asterion…' }: LoadingPageProps) {
  return (
    <div className="min-h-screen bg-surface-base flex flex-col items-center justify-center gap-6 animate-fade-in">
      {/* Animated brand icon */}
      <div className="relative flex items-center justify-center">
        {/* Outer pulse ring */}
        <span className="absolute h-20 w-20 rounded-full bg-brand-primary/10 animate-ping" />
        {/* Inner brand icon */}
        <div className="relative h-16 w-16 rounded-2xl bg-surface-primary border border-border-primary flex items-center justify-center shadow-glow-brand">
          <Radio className="h-8 w-8 text-brand-primary" />
        </div>
      </div>

      {/* Spinner + label */}
      <div className="flex flex-col items-center gap-3">
        <LoadingSpinner size="md" />
        <p className="text-sm font-medium text-content-tertiary tracking-wide">
          {label}
        </p>
      </div>
    </div>
  )
}
