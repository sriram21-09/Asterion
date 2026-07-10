import { AlertCircle, RefreshCw } from 'lucide-react'
import { cn } from '@/lib/cn'

interface ErrorCardProps {
  title?: string
  message?: string
  onRetry?: () => void
  className?: string
}

/**
 * Inline error display card.
 * Replaces ad-hoc red divs with a consistent, reusable layout.
 */
export function ErrorCard({
  title = 'Something went wrong',
  message = 'Please check your connection or try again.',
  onRetry,
  className,
}: ErrorCardProps) {
  return (
    <div
      role="alert"
      className={cn(
        'bg-danger/8 border border-danger/25 rounded-2xl p-6',
        'flex flex-col items-center text-center gap-4',
        className,
      )}
    >
      {/* Icon */}
      <div className="h-12 w-12 bg-danger/12 border border-danger/20 rounded-2xl flex items-center justify-center shrink-0">
        <AlertCircle className="h-6 w-6 text-danger" />
      </div>

      {/* Copy */}
      <div className="space-y-1">
        <h3 className="text-base font-bold text-danger">{title}</h3>
        <p className="text-sm text-content-tertiary leading-relaxed max-w-sm">
          {message}
        </p>
      </div>

      {/* Optional retry */}
      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold bg-surface-secondary border border-border-secondary text-content-secondary hover:text-content-primary hover:border-border-primary transition-all"
        >
          <RefreshCw className="h-4 w-4" />
          Try again
        </button>
      )}
    </div>
  )
}
