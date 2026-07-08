import { useEffect, useState } from 'react'
import { Plus, LayoutGrid, List } from 'lucide-react'
import { useCases, useCreateCase, useDeleteCase } from '@/hooks/useCases'
import { CaseTable } from '@/components/cases/CaseTable'
import { CaseCard } from '@/components/cases/CaseCard'
import { CaseForm } from '@/components/cases/CaseForm'
import { EmptyState } from '@/components/cases/EmptyState'
import { CreateCaseDTO } from '@/types/case'

export default function Cases() {
  const [isFormOpen, setIsFormOpen] = useState(false)
  const [viewMode, setViewMode] = useState<'list' | 'grid'>('list')

  const { data: cases, isLoading, isError, error } = useCases()
  const createCase = useCreateCase()
  const deleteCase = useDeleteCase()

  useEffect(() => {
    document.title = 'Cases — Asterion'
  }, [])

  const handleCreateCase = (data: CreateCaseDTO) => {
    createCase.mutate(data, {
      onSuccess: () => {
        setIsFormOpen(false)
      }
    })
  }

  const handleDeleteCase = (id: string) => {
    if (window.confirm('Are you sure you want to delete this case?')) {
      deleteCase.mutate(id)
    }
  }

  return (
    <div className="space-y-6 animate-fade-in relative">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-border-primary pb-5">
        <div>
          <h1 className="text-3xl font-extrabold text-content-primary tracking-tight">
            Case Management
          </h1>
          <p className="text-sm text-content-tertiary mt-1">
            Manage, search, and audit your telecom localization investigations.
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          {cases && cases.length > 0 && (
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
            <span>Create Case</span>
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-primary"></div>
        </div>
      ) : isError ? (
        <div className="bg-red-500/10 border border-red-500/20 text-red-500 rounded-2xl p-6 text-center">
          <h3 className="font-bold text-lg mb-2">Error loading cases</h3>
          <p className="text-sm opacity-80">{error?.message || 'Please check your backend connection.'}</p>
        </div>
      ) : !cases || cases.length === 0 ? (
        <EmptyState onCreateClick={() => setIsFormOpen(true)} />
      ) : (
        <>
          {viewMode === 'list' ? (
            <CaseTable 
              cases={cases} 
              onDelete={handleDeleteCase}
              isDeleting={deleteCase.isPending} 
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {cases.map((c) => (
                <CaseCard 
                  key={c.id} 
                  caseData={c} 
                  onDelete={handleDeleteCase}
                  isDeleting={deleteCase.isPending}
                />
              ))}
            </div>
          )}
        </>
      )}

      {isFormOpen && (
        <CaseForm
          onSubmit={handleCreateCase}
          onCancel={() => setIsFormOpen(false)}
          isSubmitting={createCase.isPending}
        />
      )}
    </div>
  )
}
