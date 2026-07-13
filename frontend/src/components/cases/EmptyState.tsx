import { Briefcase, Plus } from 'lucide-react';

interface EmptyStateProps {
  onCreateClick: () => void;
}

export function EmptyState({ onCreateClick }: EmptyStateProps) {
  return (
    <div className="bg-surface-primary border border-border-primary rounded-2xl p-12 text-center max-w-2xl mx-auto my-12 space-y-5 shadow-sm">
      <div className="h-20 w-20 bg-surface-secondary border border-border-secondary rounded-3xl flex items-center justify-center mx-auto shadow-inner">
        <Briefcase className="h-10 w-10 text-brand-secondary opacity-80" />
      </div>
      <div className="space-y-2">
        <h3 className="text-xl font-extrabold text-content-primary">
          No active cases found
        </h3>
        <p className="text-sm text-content-tertiary max-w-sm mx-auto leading-relaxed">
          Get started by creating a new investigation case. Cases help you organize telecom localization tasks and reports.
        </p>
      </div>
      <div className="pt-2">
        <button
          onClick={onCreateClick}
          className="inline-flex items-center space-x-2 px-6 py-3 bg-brand-primary text-white border border-brand-primary/20 rounded-xl text-sm font-semibold hover:bg-brand-primary/90 transition-all shadow-lg hover:shadow-brand-primary/20 hover:-translate-y-0.5"
        >
          <Plus className="h-4 w-4" />
          <span>Create First Case</span>
        </button>
      </div>
    </div>
  );
}
