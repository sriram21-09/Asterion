import type { Case } from '@/types/case';
import { Eye, Trash2 } from 'lucide-react';
import { cn } from '@/lib/cn';

interface CaseTableProps {
  cases: Case[];
  onDelete: (id: string) => void;
  isDeleting: boolean;
}

export function CaseTable({ cases, onDelete, isDeleting }: CaseTableProps) {
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
    <div className="w-full overflow-x-auto rounded-2xl border border-border-primary bg-surface-primary shadow-sm">
      <table className="w-full text-left text-sm text-content-secondary">
        <thead className="bg-surface-secondary text-xs uppercase text-content-secondary border-b border-border-primary">
          <tr>
            <th className="px-6 py-4 font-semibold">Reference</th>
            <th className="px-6 py-4 font-semibold">Title</th>
            <th className="px-6 py-4 font-semibold">Status</th>
            <th className="px-6 py-4 font-semibold">Date Created</th>
            <th className="px-6 py-4 font-semibold text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          {cases.map((c) => (
            <tr
              key={c.id}
              className="border-b border-border-secondary hover:bg-surface-secondary/50 transition-colors"
            >
              <td className="px-6 py-4 font-medium text-content-primary">
                {c.referenceNumber || c.id.substring(0, 8)}
              </td>
              <td className="px-6 py-4">{c.title}</td>
              <td className="px-6 py-4">
                <span
                  className={cn(
                    'px-2.5 py-1 rounded-full text-xs font-medium border uppercase tracking-wider',
                    getStatusColor(c.status)
                  )}
                >
                  {c.status.replace('_', ' ')}
                </span>
              </td>
              <td className="px-6 py-4 text-content-tertiary">
                {new Date(c.createdAt).toLocaleDateString()}
              </td>
              <td className="px-6 py-4 text-right space-x-2">
                <button
                  className="p-2 text-content-tertiary hover:text-brand-primary hover:bg-brand-primary/10 rounded-lg transition-colors"
                  title="View Case"
                >
                  <Eye className="w-4 h-4" />
                </button>
                <button
                  onClick={() => onDelete(c.id)}
                  disabled={isDeleting}
                  className="p-2 text-content-tertiary hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-colors disabled:opacity-50"
                  title="Delete Case"
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
