import { Link } from 'react-router-dom'
import { AlertCircle } from 'lucide-react'

export default function NotFound() {
  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center text-center space-y-6 animate-fade-in">
      <div className="h-16 w-16 bg-red-950/40 border border-red-500/20 rounded-2xl flex items-center justify-center">
        <AlertCircle className="h-8 w-8 text-red-400" />
      </div>
      <div className="space-y-2">
        <h1 className="text-4xl font-extrabold text-white tracking-tight">404 - Page Not Found</h1>
        <p className="text-sm text-slate-400 max-w-sm mx-auto leading-relaxed">
          The page you are looking for does not exist or has been moved.
        </p>
      </div>
      <Link 
        to="/" 
        className="inline-flex items-center justify-center px-4 py-2.5 bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:bg-slate-800 rounded-xl text-sm font-semibold transition-colors"
      >
        Return to Dashboard
      </Link>
    </div>
  )
}
