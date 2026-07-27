import { ChevronLeft, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/cn'

interface PaginationProps {
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
  className?: string
}

export function Pagination({ currentPage, totalPages, onPageChange, className }: PaginationProps) {
  if (totalPages <= 1) return null;

  return (
    <div className={cn("flex items-center justify-center space-x-2 py-4", className)}>
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className="p-1.5 rounded-lg text-content-secondary hover:bg-surface-secondary hover:text-content-primary disabled:opacity-50 disabled:cursor-not-allowed transition-colors border border-transparent hover:border-border-secondary"
      >
        <ChevronLeft className="w-4 h-4" />
      </button>
      
      <span className="text-sm text-content-secondary px-2">
        Page <span className="font-semibold text-content-primary">{currentPage}</span> of <span className="font-semibold text-content-primary">{totalPages}</span>
      </span>

      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="p-1.5 rounded-lg text-content-secondary hover:bg-surface-secondary hover:text-content-primary disabled:opacity-50 disabled:cursor-not-allowed transition-colors border border-transparent hover:border-border-secondary"
      >
        <ChevronRight className="w-4 h-4" />
      </button>
    </div>
  )
}
