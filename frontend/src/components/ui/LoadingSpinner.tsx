import { cn } from '@/lib/cn'

type SpinnerSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl'

interface LoadingSpinnerProps {
  size?: SpinnerSize
  className?: string
  label?: string
}

const sizeMap: Record<SpinnerSize, string> = {
  xs: 'h-3 w-3 border',
  sm: 'h-5 w-5 border-2',
  md: 'h-8 w-8 border-2',
  lg: 'h-12 w-12 border-[3px]',
  xl: 'h-16 w-16 border-4',
}

/**
 * Accessible animated spinner.
 * Uses brand-primary for the active arc and a muted ring for the track.
 */
export function LoadingSpinner({
  size = 'md',
  className,
  label = 'Loading…',
}: LoadingSpinnerProps) {
  return (
    <span
      role="status"
      aria-label={label}
      className={cn('inline-flex items-center justify-center', className)}
    >
      <span
        className={cn(
          'rounded-full border-surface-secondary border-t-brand-primary animate-spin',
          sizeMap[size],
        )}
      />
      <span className="sr-only">{label}</span>
    </span>
  )
}
