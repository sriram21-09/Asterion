import { Layers, Plus } from 'lucide-react';

interface EmptyStateProps {
  onCreateClick: () => void;
}

export function EmptyState({ onCreateClick }: EmptyStateProps) {
  return (
    <div className="bg-surface-primary border border-border-primary rounded-2xl p-12 text-center max-w-2xl mx-auto my-12 space-y-4">
      <div className="h-16 w-16 bg-surface-secondary border border-border-secondary rounded-2xl flex items-center justify-center mx-auto">
        <Layers className="h-8 w-8 text-brand-secondary" />
      </div>
      <div className="space-y-2">
        <h3 className="text-xl font-bold text-content-secondary">
          No scenarios configured
        </h3>
        <p className="text-sm text-content-tertiary max-w-sm mx-auto leading-relaxed">
          Get started by configuring your first mock environment. Define the layout, transmitters, bounds, and signal paths to test your localization logic.
        </p>
      </div>
      <div className="pt-4">
        <button
          onClick={onCreateClick}
          className="inline-flex items-center space-x-2 px-5 py-2.5 bg-brand-primary text-white border border-brand-primary/20 rounded-xl text-sm font-semibold hover:bg-brand-primary/90 transition-all shadow-lg shadow-brand-primary/15"
        >
          <Plus className="h-4 w-4" />
          <span>Create First Scenario</span>
        </button>
      </div>
    </div>
  );
}
