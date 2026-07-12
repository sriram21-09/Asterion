import type { Case } from '@/types/case';
import { Eye, Trash2, Calendar } from 'lucide-react';
import { cn } from '@/lib/cn';

interface CaseCardProps {
  caseData: Case;
  onDelete: (id: number) => void;
  isDeleting: boolean;
}

export function CaseCard({ caseData: c, onDelete, isDeleting }: CaseCardProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'open':
        return 'bg-green-500/10 text-green-500 border-green-500/20';
      case 'in_progress':
        return 'bg-blue-500/10 text-blue-500 border-blue-500/20';
      case 'closed':
        return 'bg-gray-500/10 text-gray-400 border-gray-500/20';
      default:
        return 'bg-surface-secondary text-content-secondary border-border-secondary';
    }
  };

  return (
    <div className="bg-surface-primary border border-border-primary rounded-2xl p-5 hover:border-brand-primary/50 transition-all shadow-sm flex flex-col h-full group">
      <div className="flex justify-between items-start mb-4">
        <div>
          <span className="text-xs font-semibold text-content-tertiary uppercase tracking-wider mb-1 block">
            Case #{c.id}
          </span>
          <h3 className="text-lg font-bold text-content-primary line-clamp-1 group-hover:text-brand-primary transition-colors">
            {c.title}
          </h3>
        </div>
        <span
          className={cn(
            'px-2 py-0.5 rounded-full text-[10px] font-bold border uppercase tracking-widest shrink-0',
            getStatusColor(c.status)
          )}
        >
          {c.status.replace('_', ' ')}
        </span>
      </div>
      
      <p className="text-sm text-content-secondary line-clamp-2 mb-6 flex-grow">
        {c.description || 'No description provided.'}
      </p>

      <div className="pt-4 border-t border-border-secondary flex items-center justify-between mt-auto">
        <div className="flex items-center text-content-tertiary text-xs">
          <Calendar className="w-3.5 h-3.5 mr-1.5" />
          {new Date(c.created_at).toLocaleDateString()}
        </div>
        
        <div className="flex items-center space-x-1">
          <button
            className="p-1.5 text-content-tertiary hover:text-brand-primary hover:bg-brand-primary/10 rounded-md transition-colors"
            title="View Details"
          >
            <Eye className="w-4 h-4" />
          </button>
          <button
            onClick={() => onDelete(c.id)}
            disabled={isDeleting}
            className="p-1.5 text-content-tertiary hover:text-red-500 hover:bg-red-500/10 rounded-md transition-colors disabled:opacity-50"
            title="Delete Case"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
