import type { Scenario } from '@/types/scenario';
import { Eye, Trash2, Calendar } from 'lucide-react';

interface ScenarioCardProps {
  scenarioData: Scenario;
  onDelete: (id: number) => void;
  isDeleting: boolean;
}

export function ScenarioCard({ scenarioData: s, onDelete, isDeleting }: ScenarioCardProps) {
  return (
    <div className="bg-surface-primary border border-border-primary rounded-2xl p-5 hover:border-brand-primary/50 transition-all shadow-sm flex flex-col h-full group">
      <div className="flex justify-between items-start mb-4">
        <div>
          <span className="text-xs font-semibold text-content-tertiary uppercase tracking-wider mb-1 block">
            Scenario #{s.id}
          </span>
          <h3 className="text-lg font-bold text-content-primary line-clamp-1 group-hover:text-brand-primary transition-colors">
            {s.name}
          </h3>
        </div>
      </div>

      <p className="text-sm text-content-secondary line-clamp-2 mb-6 flex-grow">
        {s.description || 'No description provided.'}
      </p>

      <div className="pt-4 border-t border-border-secondary flex items-center justify-between mt-auto">
        <div className="flex items-center text-content-tertiary text-xs">
          <Calendar className="w-3.5 h-3.5 mr-1.5" />
          {new Date(s.created_at).toLocaleDateString()}
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
