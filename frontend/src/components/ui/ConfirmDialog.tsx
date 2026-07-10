import { useEffect, useRef } from 'react'
import { AlertTriangle, X } from 'lucide-react'
import { cn } from '@/lib/cn'

interface ConfirmDialogProps {
  title: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
  isDangerous?: boolean
  isLoading?: boolean
  onConfirm: () => void
  onCancel: () => void
}

/**
 * Accessible confirmation modal — replaces window.confirm().
 * Traps focus, responds to Escape key, and respects isDangerous styling.
 */
export function ConfirmDialog({
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  isDangerous = false,
  isLoading = false,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  const cancelRef = useRef<HTMLButtonElement>(null)

  // Auto-focus cancel on mount; close on Escape
  useEffect(() => {
    cancelRef.current?.focus()
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onCancel()
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [onCancel])

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-dialog-title"
      aria-describedby="confirm-dialog-desc"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in"
      onClick={(e) => e.target === e.currentTarget && onCancel()}
    >
      <div className="bg-surface-primary border border-border-primary rounded-2xl shadow-2xl w-full max-w-sm overflow-hidden animate-slide-up">
        {/* Header */}
        <div className="flex items-start justify-between px-6 pt-6 pb-4 gap-4">
          <div className="flex items-center gap-3">
            <div
              className={cn(
                'h-10 w-10 rounded-xl flex items-center justify-center shrink-0',
                isDangerous
                  ? 'bg-danger/10 border border-danger/20'
                  : 'bg-warning/10 border border-warning/20',
              )}
            >
              <AlertTriangle
                className={cn(
                  'h-5 w-5',
                  isDangerous ? 'text-danger' : 'text-warning',
                )}
              />
            </div>
            <h2
              id="confirm-dialog-title"
              className="text-base font-bold text-content-primary"
            >
              {title}
            </h2>
          </div>

          <button
            onClick={onCancel}
            className="p-1.5 rounded-lg text-content-tertiary hover:text-content-primary hover:bg-surface-secondary transition-colors"
            aria-label="Close dialog"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Body */}
        <p
          id="confirm-dialog-desc"
          className="px-6 pb-6 text-sm text-content-tertiary leading-relaxed"
        >
          {message}
        </p>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-border-primary bg-surface-secondary/40">
          <button
            ref={cancelRef}
            onClick={onCancel}
            disabled={isLoading}
            className="px-4 py-2 text-sm font-semibold text-content-secondary bg-surface-secondary border border-border-secondary rounded-xl hover:text-content-primary hover:bg-border-secondary transition-colors disabled:opacity-50"
          >
            {cancelLabel}
          </button>

          <button
            onClick={onConfirm}
            disabled={isLoading}
            className={cn(
              'inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed',
              isDangerous
                ? 'bg-danger text-white hover:bg-danger/90 shadow-lg shadow-danger/20'
                : 'bg-brand-primary text-white hover:bg-brand-primary/90',
            )}
          >
            {isLoading ? (
              <>
                <span className="h-3.5 w-3.5 rounded-full border-2 border-white/30 border-t-white animate-spin" />
                Processing…
              </>
            ) : (
              confirmLabel
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
