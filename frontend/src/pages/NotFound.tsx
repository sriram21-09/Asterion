import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { AlertCircle } from 'lucide-react'

export default function NotFound() {
  useEffect(() => {
    document.title = '404 — Asterion'
  }, [])

  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center text-center space-y-6 animate-fade-in">
      <div className="h-16 w-16 bg-danger/10 border border-danger/20 rounded-2xl flex items-center justify-center">
        <AlertCircle className="h-8 w-8 text-danger" />
      </div>
      <div className="space-y-2">
        <h1 className="text-4xl font-extrabold text-content-primary tracking-tight">
          404 — Page Not Found
        </h1>
        <p className="text-sm text-content-tertiary max-w-sm mx-auto leading-relaxed">
          The page you are looking for does not exist or has been moved.
        </p>
      </div>
      <Link
        to="/"
        className="inline-flex items-center justify-center px-4 py-2.5 bg-surface-primary border border-border-primary text-content-secondary hover:text-content-primary hover:bg-surface-secondary rounded-xl text-sm font-semibold transition-colors"
      >
        Return to Dashboard
      </Link>
    </div>
  )
}
