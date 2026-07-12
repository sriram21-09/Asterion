import { cn } from '@/lib/cn'

interface SkeletonCardProps {
  /** Number of text line skeletons to render */
  lines?: number
  /** Show a larger header line */
  showHeader?: boolean
  /** Show a badge/chip skeleton in the top-right */
  showBadge?: boolean
  className?: string
}

/** A single shimmer skeleton block */
function SkeletonBlock({ className }: { className?: string }) {
  return (
    <div
      className={cn('rounded-lg skeleton-shimmer', className)}
      aria-hidden="true"
    />
  )
}

/**
 * Animated shimmer placeholder card.
 * Drop this in place of real content while data is loading.
 */
export function SkeletonCard({
  lines = 3,
  showHeader = true,
  showBadge = true,
  className,
}: SkeletonCardProps) {
  return (
    <div
      className={cn(
        'bg-surface-primary border border-border-primary rounded-2xl p-5 space-y-4',
        className,
      )}
      aria-busy="true"
      aria-label="Loading…"
    >
      {/* Header row */}
      {showHeader && (
        <div className="flex items-center justify-between gap-3">
          <SkeletonBlock className="h-5 w-2/3" />
          {showBadge && <SkeletonBlock className="h-5 w-16 rounded-full" />}
        </div>
      )}

      {/* Text lines */}
      <div className="space-y-2.5">
        {Array.from({ length: lines }).map((_, i) => (
          <SkeletonBlock
            key={i}
            className={cn('h-3', i === lines - 1 ? 'w-3/5' : 'w-full')}
          />
        ))}
      </div>

      {/* Footer action row */}
      <div className="flex items-center justify-between pt-1 border-t border-border-primary">
        <SkeletonBlock className="h-3 w-24" />
        <SkeletonBlock className="h-7 w-20 rounded-lg" />
      </div>
    </div>
  )
}

/** Render N skeleton cards in a grid — convenience wrapper */
export function SkeletonGrid({
  count = 3,
  className,
}: {
  count?: number
  className?: string
}) {
  return (
    <div
      className={cn(
        'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5',
        className,
      )}
    >
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  )
}
