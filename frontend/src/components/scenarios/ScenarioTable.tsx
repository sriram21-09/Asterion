import type { Scenario } from '@/types/scenario';
import { Eye, Trash2 } from 'lucide-react';

interface ScenarioTableProps {
  scenarios: Scenario[];
  onDelete: (id: number) => void;
  isDeleting: boolean;
}

export function ScenarioTable({ scenarios, onDelete, isDeleting }: ScenarioTableProps) {
  return (
    <div className="w-full overflow-x-auto rounded-2xl border border-border-primary bg-surface-primary shadow-sm">
      <table className="w-full text-left text-sm text-content-secondary">
        <thead className="bg-surface-secondary text-xs uppercase text-content-secondary border-b border-border-primary">
          <tr>
            <th className="px-6 py-4 font-semibold">#</th>
            <th className="px-6 py-4 font-semibold">Name</th>
            <th className="px-6 py-4 font-semibold">Description</th>
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
                #{s.id}
              </td>
              <td className="px-6 py-4 font-medium text-content-primary">{s.name}</td>
              <td className="px-6 py-4 text-content-tertiary max-w-xs truncate">
                {s.description || '—'}
              </td>
              <td className="px-6 py-4 text-content-tertiary">
                {new Date(s.created_at).toLocaleDateString()}
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
