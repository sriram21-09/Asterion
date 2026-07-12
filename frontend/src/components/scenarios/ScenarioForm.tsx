import { useState } from 'react';
import type { CreateScenarioDTO } from '@/types/scenario';
import { X, Loader2, Save } from 'lucide-react';

interface ScenarioFormProps {
  onSubmit: (data: CreateScenarioDTO) => void;
  onCancel: () => void;
  isSubmitting: boolean;
}

export function ScenarioForm({ onSubmit, onCancel, isSubmitting }: ScenarioFormProps) {
  const [formData, setFormData] = useState<CreateScenarioDTO>({
    name: '',
    description: '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) return;
    onSubmit(formData);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in">
      <div className="bg-surface-primary border border-border-primary w-full max-w-lg rounded-2xl shadow-2xl overflow-hidden animate-slide-up">
        <div className="px-6 py-4 border-b border-border-primary flex items-center justify-between bg-surface-secondary/50">
          <h2 className="text-xl font-bold text-content-primary">Create New Scenario</h2>
          <button
            onClick={onCancel}
            className="p-2 text-content-tertiary hover:text-content-primary hover:bg-surface-secondary rounded-xl transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          <div className="space-y-1.5">
            <label htmlFor="scenario-name" className="text-sm font-semibold text-content-secondary">
              Scenario Name <span className="text-red-500">*</span>
            </label>
            <input
              id="scenario-name"
              type="text"
              required
              className="w-full bg-surface-secondary border border-border-secondary rounded-xl px-4 py-2.5 text-content-primary focus:outline-none focus:ring-2 focus:ring-brand-primary/50 focus:border-brand-primary transition-all"
              placeholder="e.g. Downtown Metro RF Test"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            />
          </div>

          <div className="space-y-1.5">
            <label htmlFor="scenario-description" className="text-sm font-semibold text-content-secondary">
              Description (Optional)
            </label>
            <textarea
              id="scenario-description"
              rows={3}
              className="w-full bg-surface-secondary border border-border-secondary rounded-xl px-4 py-2.5 text-content-primary focus:outline-none focus:ring-2 focus:ring-brand-primary/50 focus:border-brand-primary transition-all resize-none"
              placeholder="Describe the objective or terrain conditions..."
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            />
          </div>

          <div className="pt-4 flex items-center justify-end space-x-3 border-t border-border-secondary mt-2">
            <button
              type="button"
              onClick={onCancel}
              className="px-5 py-2.5 text-sm font-semibold text-content-secondary hover:text-content-primary bg-surface-secondary hover:bg-border-secondary border border-transparent rounded-xl transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !formData.name.trim()}
              className="inline-flex items-center space-x-2 px-5 py-2.5 text-sm font-semibold text-white bg-brand-primary hover:bg-brand-primary/90 border border-brand-primary/20 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-brand-primary/15"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Creating...</span>
                </>
              ) : (
                <>
                  <Save className="w-4 h-4" />
                  <span>Create Scenario</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
