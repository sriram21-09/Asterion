import { useEffect, useState } from 'react'
import { Plus, LayoutGrid, List } from 'lucide-react'
import { useScenarios, useCreateScenario, useDeleteScenario } from '@/hooks/useScenarios'
import { ScenarioTable } from '@/components/scenarios/ScenarioTable'
import { ScenarioCard } from '@/components/scenarios/ScenarioCard'
import { ScenarioForm } from '@/components/scenarios/ScenarioForm'
import { EmptyState } from '@/components/scenarios/EmptyState'
import type { CreateScenarioDTO } from '@/types/scenario'

export default function Scenarios() {
  const [isFormOpen, setIsFormOpen] = useState(false)
  const [viewMode, setViewMode] = useState<'list' | 'grid'>('list')

  const { data: scenarios, isLoading, isError, error } = useScenarios()
  const createScenario = useCreateScenario()
  const deleteScenario = useDeleteScenario()

  useEffect(() => {
    document.title = 'Scenarios — Asterion'
  }, [])

  const handleCreateScenario = (data: CreateScenarioDTO) => {
    createScenario.mutate(data, {
      onSuccess: () => {
        setIsFormOpen(false)
      }
    })
  }

  const handleDeleteScenario = (id: string) => {
    if (window.confirm('Are you sure you want to delete this scenario?')) {
      deleteScenario.mutate(id)
    }
  }

  return (
    <div className="space-y-6 animate-fade-in relative">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-border-primary pb-5">
        <div>
          <h1 className="text-3xl font-extrabold text-content-primary tracking-tight">
            Scenarios Configurator
          </h1>
          <p className="text-sm text-content-tertiary mt-1">
            Configure layout, transmitters, bounds, and signal paths.
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          {scenarios && scenarios.length > 0 && (
            <div className="flex bg-surface-secondary border border-border-secondary rounded-lg p-1">
              <button
                onClick={() => setViewMode('list')}
                className={`p-1.5 rounded-md transition-all ${
                  viewMode === 'list' 
                    ? 'bg-surface-primary shadow text-brand-primary' 
                    : 'text-content-tertiary hover:text-content-secondary'
                }`}
                title="List View"
              >
                <List className="w-4 h-4" />
              </button>
              <button
                onClick={() => setViewMode('grid')}
                className={`p-1.5 rounded-md transition-all ${
                  viewMode === 'grid' 
                    ? 'bg-surface-primary shadow text-brand-primary' 
                    : 'text-content-tertiary hover:text-content-secondary'
                }`}
                title="Grid View"
              >
                <LayoutGrid className="w-4 h-4" />
              </button>
            </div>
          )}

          <button
            onClick={() => setIsFormOpen(true)}
            className="inline-flex items-center space-x-2 px-4 py-2.5 bg-brand-primary text-brand-secondary border border-brand-primary/20 rounded-xl text-sm font-semibold hover:bg-brand-primary/90 transition-all shadow-[0_0_15px_rgba(255,255,255,0.1)]"
          >
            <Plus className="h-4 w-4" />
            <span>Add Scenario</span>
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-primary"></div>
        </div>
      ) : isError ? (
        <div className="bg-red-500/10 border border-red-500/20 text-red-500 rounded-2xl p-6 text-center">
          <h3 className="font-bold text-lg mb-2">Error loading scenarios</h3>
          <p className="text-sm opacity-80">{error?.message || 'Please check your backend connection.'}</p>
        </div>
      ) : !scenarios || scenarios.length === 0 ? (
        <EmptyState onCreateClick={() => setIsFormOpen(true)} />
      ) : (
        <>
          {viewMode === 'list' ? (
            <ScenarioTable 
              scenarios={scenarios} 
              onDelete={handleDeleteScenario}
              isDeleting={deleteScenario.isPending} 
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {scenarios.map((s) => (
                <ScenarioCard 
                  key={s.id} 
                  scenarioData={s} 
                  onDelete={handleDeleteScenario}
                  isDeleting={deleteScenario.isPending}
                />
              ))}
            </div>
          )}
        </>
      )}

      {isFormOpen && (
        <ScenarioForm
          onSubmit={handleCreateScenario}
          onCancel={() => setIsFormOpen(false)}
          isSubmitting={createScenario.isPending}
        />
      )}
    </div>
  )
}
