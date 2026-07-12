import { useEffect } from 'react'
import { Link, useRouteError, isRouteErrorResponse } from 'react-router-dom'
import { AlertTriangle, RefreshCw, ArrowLeft } from 'lucide-react'

/**
 * Generic error boundary fallback page.
 * Works as a React Router v7 errorElement — receives the route error via
 * useRouteError(). Falls back gracefully for non-route errors too.
 */
export default function ErrorPage() {
  const error = useRouteError()

  let title = 'Something went wrong'
  let message = 'An unexpected error occurred. Please try refreshing the page.'
  let statusCode: number | null = null

  if (isRouteErrorResponse(error)) {
    statusCode = error.status
    title = `${error.status} — ${error.statusText}`
    message =
      typeof error.data === 'string'
        ? error.data
        : 'The server returned an error response.'
  } else if (error instanceof Error) {
    message = error.message
  }

  useEffect(() => {
    document.title = `Error — Asterion`
  }, [])

  return (
    <div className="min-h-screen bg-surface-base flex flex-col items-center justify-center px-6 py-16 animate-fade-in">
      {/* Icon */}
      <div className="relative mb-8">
        <div className="absolute inset-0 bg-danger/8 blur-3xl rounded-full scale-150 pointer-events-none" />
        <div className="relative h-20 w-20 mx-auto rounded-3xl bg-surface-primary border border-danger/20 flex items-center justify-center">
          <AlertTriangle className="h-10 w-10 text-danger" />
        </div>
      </div>

      {/* Status code */}
      {statusCode && (
        <p className="text-7xl font-black text-content-primary opacity-10 mb-2 select-none">
          {statusCode}
        </p>
      )}

      {/* Copy */}
      <div className="space-y-3 text-center max-w-md mb-10">
        <h1 className="text-2xl font-extrabold text-content-primary tracking-tight">
          {title}
        </h1>
        <p className="text-sm text-content-tertiary leading-relaxed">{message}</p>

        {/* Dev-only stack trace */}
        {import.meta.env.DEV && error instanceof Error && error.stack && (
          <details className="mt-4 text-left">
            <summary className="text-xs text-content-tertiary cursor-pointer hover:text-content-secondary transition-colors">
              Stack trace
            </summary>
            <pre className="mt-2 p-3 bg-surface-secondary border border-border-primary rounded-xl text-xs text-content-tertiary overflow-x-auto whitespace-pre-wrap">
              {error.stack}
            </pre>
          </details>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => window.location.reload()}
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-brand-primary text-white text-sm font-semibold rounded-xl hover:bg-brand-primary/90 transition-all"
        >
          <RefreshCw className="h-4 w-4" />
          Reload page
        </button>

        <Link
          to="/"
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-surface-primary border border-border-primary text-content-secondary text-sm font-semibold rounded-xl hover:text-content-primary hover:bg-surface-secondary transition-all"
        >
          <ArrowLeft className="h-4 w-4" />
          Dashboard
        </Link>
      </div>
    </div>
  )
}
