import { CheckCircle2, Circle, Loader2, HeartPulse } from 'lucide-react';
import { cn } from '@/lib/cn';

interface PipelineStage {
  name: string;
  status: 'completed' | 'running' | 'pending';
  description: string;
}

interface InvestigationHealthCardProps {
  hasMeasurements: boolean;
  isGenerating: boolean;
  isValidated: boolean;
  isValidating: boolean;
  hasTowersResolved: boolean;
  isLocalizing: boolean;
  hasMovement: boolean;
  isTracking: boolean;
  hasLocalization: boolean;
  hasConfidence: boolean;
  isAnalyzing: boolean;
  hasEvidence: boolean;
  isFetchingEvidence: boolean;
}

export function InvestigationHealthCard({
  hasMeasurements,
  isGenerating,
  isValidated,
  isValidating,
  hasTowersResolved,
  isLocalizing,
  hasMovement,
  isTracking,
  hasLocalization,
  hasConfidence,
  isAnalyzing,
  hasEvidence,
  isFetchingEvidence,
}: InvestigationHealthCardProps) {
  
  const stages: PipelineStage[] = [
    {
      name: 'Imported',
      status: isGenerating ? 'running' : hasMeasurements ? 'completed' : 'pending',
      description: 'Raw CDR measurement records successfully imported.',
    },
    {
      name: 'Validated',
      status: isValidating ? 'running' : isValidated ? 'completed' : 'pending',
      description: 'Data checked for boundary, duplication, and formatting errors.',
    },
    {
      name: 'Towers Resolved',
      status: isLocalizing ? 'running' : hasTowersResolved ? 'completed' : 'pending',
      description: 'Cell tower coordinates matched and resolved from database.',
    },
    {
      name: 'Movement Reconstructed',
      status: isTracking ? 'running' : hasMovement ? 'completed' : 'pending',
      description: 'Continuous travel path generated via Kalman filtering.',
    },
    {
      name: 'Localization Complete',
      status: isLocalizing ? 'running' : hasLocalization ? 'completed' : 'pending',
      description: 'Estimated device location optimized via NLLS solver.',
    },
    {
      name: 'Confidence Generated',
      status: isAnalyzing ? 'running' : hasConfidence ? 'completed' : 'pending',
      description: 'GDOP and uncertainty ellipses calculated.',
    },
    {
      name: 'Evidence Logged',
      status: isFetchingEvidence ? 'running' : hasEvidence ? 'completed' : 'pending',
      description: 'Immutable verification audit trail signed and ready.',
    },
    {
      name: 'Report Ready',
      status: hasEvidence && hasConfidence && hasMovement && hasLocalization ? 'completed' : 'pending',
      description: 'Comprehensive investigation dossier compiled.',
    },
  ];

  // Calculate overall health score (completed stages out of total)
  const completedCount = stages.filter((s) => s.status === 'completed').length;
  const healthPercent = Math.round((completedCount / stages.length) * 100);

  return (
    <div className="glass-card rounded-2xl p-6 border border-border-primary flex flex-col bg-surface-primary/30 h-full">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <HeartPulse className="h-5 w-5 text-brand-primary" />
          <h2 className="text-lg font-bold text-content-primary">Investigation Health</h2>
        </div>
        <span className={cn(
          "px-2.5 py-1 rounded-full text-xs font-bold border",
          healthPercent === 100 ? "bg-success/10 border-success/20 text-success" :
          healthPercent >= 50 ? "bg-brand-primary/10 border-brand-primary/20 text-brand-primary" :
          "bg-surface-secondary border-border-secondary text-content-tertiary"
        )}>
          {healthPercent}% Ready
        </span>
      </div>

      {/* Progress Bar */}
      <div className="h-2 w-full bg-surface-secondary rounded-full overflow-hidden border border-border-secondary/20 mb-6 shrink-0">
        <div 
          className="h-full bg-brand-primary rounded-full transition-all duration-500"
          style={{ width: `${healthPercent}%` }}
        />
      </div>

      {/* Stages List */}
      <div className="space-y-4 overflow-y-auto flex-1 pr-1 max-h-[400px]">
        {stages.map((stage, idx) => {
          return (
            <div key={stage.name} className="flex items-start space-x-3 group">
              <div className="shrink-0 mt-0.5 relative flex items-center justify-center">
                {stage.status === 'completed' ? (
                  <CheckCircle2 className="h-4.5 w-4.5 text-success fill-success/10" />
                ) : stage.status === 'running' ? (
                  <Loader2 className="h-4.5 w-4.5 text-brand-primary animate-spin" />
                ) : (
                  <Circle className="h-4.5 w-4.5 text-content-tertiary" />
                )}
                {idx < stages.length - 1 && (
                  <div className={cn(
                    "absolute top-5 bottom-[-18px] left-[8px] w-0.5",
                    stage.status === 'completed' ? "bg-success" : "bg-border-secondary"
                  )} />
                )}
              </div>
              <div className="min-w-0">
                <p className={cn(
                  "text-xs font-bold transition-colors",
                  stage.status === 'completed' ? "text-content-primary" :
                  stage.status === 'running' ? "text-brand-primary" : "text-content-tertiary"
                )}>
                  {stage.name}
                </p>
                <p className="text-[10px] text-content-tertiary leading-normal mt-0.5 truncate group-hover:whitespace-normal group-hover:overflow-visible">
                  {stage.description}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
