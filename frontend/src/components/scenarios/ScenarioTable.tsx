import type { Scenario } from '@/types/scenario';
import { Eye, Trash2 } from 'lucide-react';
import { cn } from '@/lib/cn';

interface ScenarioTableProps {
  scenarios: Scenario[];
  onDelete: (id: string) => void;
  isDeleting: boolean;
}

export function ScenarioTable({ scenarios, onDelete, isDeleting }: ScenarioTableProps) {
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
    <div className="w-full overflow-x-auto rounded-2xl border border-border-primary bg-surface-primary shadow-sm">
      <table className="w-full text-left text-sm text-content-secondary">
        <thead className="bg-surface-secondary text-xs uppercase text-content-secondary border-b border-border-primary">
          <tr>
            <th className="px-6 py-4 font-semibold">ID</th>
            <th className="px-6 py-4 font-semibold">Title</th>
            <th className="px-6 py-4 font-semibold">Environment</th>
            <th className="px-6 py-4 font-semibold">Status</th>
            <th className="px-6 py-4 font-semibold">Date Created</th>
            <th className="px-6 py-4 font-semibold text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          {scenarios.map((s) => (
            <tr
              key={s.id}
              className="border-b border-border-secondary hover:bg-surface-secondary/50 transition-colors"
            >
              <td className="px-6 py-4 font-medium text-content-primary">
                {s.id.substring(0, 8)}
              </td>
              <td className="px-6 py-4">{s.title}</td>
              <td className="px-6 py-4 capitalize">{s.environmentType}</td>
              <td className="px-6 py-4">
                <span
                  className={cn(
                    'px-2.5 py-1 rounded-full text-xs font-medium border uppercase tracking-wider',
                    getStatusColor(s.status)
                  )}
                >
                  {s.status}
                </span>
              </td>
              <td className="px-6 py-4 text-content-tertiary">
                {new Date(s.createdAt).toLocaleDateString()}
              </td>
              <td className="px-6 py-4 text-right space-x-2">
                <button
                  className="p-2 text-content-tertiary hover:text-brand-primary hover:bg-brand-primary/10 rounded-lg transition-colors"
                  title="View Scenario"
                >
                  <Eye className="w-4 h-4" />
                </button>
                <button
                  onClick={() => onDelete(s.id)}
                  disabled={isDeleting}
                  className="p-2 text-content-tertiary hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-colors disabled:opacity-50"
                  title="Delete Scenario"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
