import { cn } from '@/lib/cn'

type BadgeVariant = 'default' | 'success' | 'warning' | 'danger' | 'info' | 'muted'

interface BadgeProps {
  variant?: BadgeVariant
  children: React.ReactNode
  className?: string
  dot?: boolean
}

const variantStyles: Record<BadgeVariant, string> = {
  default:
    'bg-surface-secondary border-border-secondary text-content-secondary',
  success:
    'bg-success/10 border-success/25 text-success',
  warning:
    'bg-warning/10 border-warning/25 text-warning',
  danger:
    'bg-danger/10 border-danger/25 text-danger',
  info:
    'bg-info/10 border-info/25 text-info',
  muted:
    'bg-surface-tertiary border-border-primary text-content-tertiary',
}

const dotStyles: Record<BadgeVariant, string> = {
  default:  'bg-content-tertiary',
  success:  'bg-success',
  warning:  'bg-warning',
  danger:   'bg-danger',
  info:     'bg-info',
  muted:    'bg-content-tertiary',
}

/**
 * Compact status badge.
 * Use `dot` prop to add a small colored circle before the label.
 */
export function Badge({
  variant = 'default',
  children,
  className,
  dot = false,
}: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold border',
        variantStyles[variant],
        className,
      )}
    >
      {dot && (
        <span
          className={cn('h-1.5 w-1.5 rounded-full shrink-0', dotStyles[variant])}
        />
      )}
      {children}
    </span>
  )
}
