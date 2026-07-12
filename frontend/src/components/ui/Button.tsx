import { forwardRef } from 'react'
import { Loader2 } from 'lucide-react'
import { cn } from '@/lib/cn'

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger'
type ButtonSize = 'sm' | 'md' | 'lg'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  isLoading?: boolean
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
}

const variantStyles: Record<ButtonVariant, string> = {
  primary: [
    'bg-brand-primary text-white border border-brand-primary/20',
    'hover:bg-brand-primary/90 shadow-lg shadow-brand-primary/15',
    'disabled:opacity-50',
  ].join(' '),
  secondary: [
    'bg-surface-secondary text-content-secondary border border-border-secondary',
    'hover:bg-border-secondary hover:text-content-primary',
    'disabled:opacity-50',
  ].join(' '),
  ghost: [
    'bg-transparent text-content-tertiary border border-transparent',
    'hover:bg-surface-secondary hover:text-content-primary',
    'disabled:opacity-50',
  ].join(' '),
  danger: [
    'bg-danger text-white border border-danger/20',
    'hover:bg-danger/90 shadow-lg shadow-danger/15',
    'disabled:opacity-50',
  ].join(' '),
}

const sizeStyles: Record<ButtonSize, string> = {
  sm: 'h-8 px-3 text-xs gap-1.5 rounded-lg',
  md: 'h-10 px-4 text-sm gap-2 rounded-xl',
  lg: 'h-11 px-5 text-sm gap-2.5 rounded-xl',
}

/**
 * Polymorphic button primitive with variants, sizes, loading state,
 * and optional leading/trailing icons.
 */
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      isLoading = false,
      leftIcon,
      rightIcon,
      disabled,
      children,
      className,
      ...props
    },
    ref,
  ) => {
    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(
          'inline-flex items-center justify-center font-semibold transition-all duration-200',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary/50',
          'disabled:cursor-not-allowed',
          variantStyles[variant],
          sizeStyles[size],
          className,
        )}
        {...props}
      >
        {isLoading ? (
          <Loader2 className="h-4 w-4 animate-spin shrink-0" />
        ) : (
          leftIcon && <span className="shrink-0">{leftIcon}</span>
        )}
        {children}
        {!isLoading && rightIcon && (
          <span className="shrink-0">{rightIcon}</span>
        )}
      </button>
    )
  },
)

Button.displayName = 'Button'
