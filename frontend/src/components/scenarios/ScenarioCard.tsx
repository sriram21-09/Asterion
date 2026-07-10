import type { Scenario } from '@/types/scenario';
import { Eye, Trash2, Calendar, MapPin } from 'lucide-react';
import { cn } from '@/lib/cn';

interface ScenarioCardProps {
  scenarioData: Scenario;
  onDelete: (id: string) => void;
  isDeleting: boolean;
}

export function ScenarioCard({ scenarioData: s, onDelete, isDeleting }: ScenarioCardProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20';
      case 'draft':
        return 'bg-amber-500/10 text-amber-500 border-amber-500/20';
      case 'archived':
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
            {s.id.substring(0, 8)}
          </span>
          <h3 className="text-lg font-bold text-content-primary line-clamp-1 group-hover:text-brand-primary transition-colors">
            {s.title}
          </h3>
        </div>
        <span
          className={cn(
            'px-2 py-0.5 rounded-full text-[10px] font-bold border uppercase tracking-widest shrink-0',
            getStatusColor(s.status)
          )}
        >
          {s.status}
        </span>
      </div>
      
      <div className="flex items-center text-xs text-brand-primary font-medium mb-3">
        <MapPin className="w-3.5 h-3.5 mr-1" />
        <span className="capitalize">{s.environmentType}</span>
      </div>
      
      <p className="text-sm text-content-secondary line-clamp-2 mb-6 flex-grow">
        {s.description || 'No description provided.'}
      </p>

      <div className="pt-4 border-t border-border-secondary flex items-center justify-between mt-auto">
        <div className="flex items-center text-content-tertiary text-xs">
          <Calendar className="w-3.5 h-3.5 mr-1.5" />
          {new Date(s.createdAt).toLocaleDateString()}
        </div>
        
        <div className="flex items-center space-x-1">
          <button
            className="p-1.5 text-content-tertiary hover:text-brand-primary hover:bg-brand-primary/10 rounded-md transition-colors"
            title="View Details"
          >
            <Eye className="w-4 h-4" />
          </button>
          <button
            onClick={() => onDelete(s.id)}
            disabled={isDeleting}
            className="p-1.5 text-content-tertiary hover:text-red-500 hover:bg-red-500/10 rounded-md transition-colors disabled:opacity-50"
            title="Delete Scenario"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
