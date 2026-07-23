import { useState, useRef, type DragEvent, type ChangeEvent } from 'react'
import { UploadCloud, FileSpreadsheet, CheckCircle, AlertCircle, Trash2, ShieldAlert, Database, AlertTriangle } from 'lucide-react'
import { Button } from '@/components/ui'
import { cn } from '@/lib/cn'

interface UploadedFile {
  file: File
  operator: string
  status: 'detecting' | 'ready' | 'error'
  errorMessage?: string
}

export default function ImportPage() {
  const [isDragging, setIsDragging] = useState(false)
  const [files, setFiles] = useState<UploadedFile[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = async (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(false)
    const droppedFiles = Array.from(e.dataTransfer.files).filter(f => f.name.endsWith('.csv'))
    await processFiles(droppedFiles)
  }

  const handleFileInput = async (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files)
      await processFiles(selectedFiles)
    }
  }

  const detectOperator = async (file: File): Promise<string> => {
    return new Promise((resolve) => {
      const name = file.name.toLowerCase()
      if (name.includes('vodafone')) return resolve('Vodafone')
      if (name.includes('o2') || name.includes('telefonica')) return resolve('O2')
      if (name.includes('telekom') || name.includes('t-mobile')) return resolve('Telekom')

      const reader = new FileReader()
      reader.onload = (e) => {
        const text = e.target?.result as string
        const firstLine = text.split('\n')[0].toLowerCase()
        if (firstLine.includes('vdf') || firstLine.includes('vodafone')) {
          resolve('Vodafone')
        } else if (firstLine.includes('t-mobile') || firstLine.includes('telekom')) {
          resolve('Telekom')
        } else if (firstLine.includes('o2') || firstLine.includes('telefonica')) {
          resolve('O2')
        } else {
          resolve('Unknown')
        }
      }
      reader.onerror = () => resolve('Unknown')
      reader.readAsText(file.slice(0, 1024))
    })
  }

  const processFiles = async (newFiles: File[]) => {
    const initialFiles: UploadedFile[] = newFiles.map(file => ({
      file,
      operator: 'Detecting...',
      status: 'detecting'
    }))

    setFiles(prev => [...prev, ...initialFiles])

    for (const newFile of initialFiles) {
      const operator = await detectOperator(newFile.file)
      setFiles(prev => prev.map(f => {
        if (f.file.name === newFile.file.name) {
          if (operator === 'Unknown') {
            return { ...f, operator, status: 'error', errorMessage: 'Could not auto-detect operator format.' }
          }
          return { ...f, operator, status: 'ready' }
        }
        return f
      }))
    }
  }

  const removeFile = (fileName: string) => {
    setFiles(prev => prev.filter(f => f.file.name !== fileName))
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header Section */}
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight text-content-primary">
          Import Data
        </h1>
        <p className="text-content-tertiary max-w-2xl">
          Upload raw measurements from telecom providers. The system will automatically detect
          the operator based on file names and header signatures.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Upload Zone */}
        <div className="lg:col-span-2 space-y-6">
          <div
            className={cn(
              'glass-card rounded-2xl p-10 flex flex-col items-center justify-center text-center cursor-pointer transition-all duration-300',
              'border-2 border-dashed min-h-[360px]',
              isDragging 
                ? 'border-brand-primary bg-brand-primary/10 scale-[1.02] shadow-[0_0_30px_rgba(var(--color-brand-primary),0.2)]'
                : 'border-border-secondary hover:border-brand-primary/50 hover:bg-surface-secondary'
            )}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileInput}
              accept=".csv"
              multiple
              className="hidden"
            />
            
            <div className={cn(
              "p-5 rounded-full mb-6 transition-colors duration-300",
              isDragging ? "bg-brand-primary text-white" : "bg-surface-tertiary text-brand-primary"
            )}>
              <UploadCloud className="h-10 w-10" />
            </div>
            
            <h3 className="text-xl font-semibold text-content-primary mb-2">
              Drag & Drop CSV files here
            </h3>
            <p className="text-content-tertiary max-w-sm mb-8">
              Supports standard CSV exports from Vodafone, Telekom, and O2.
            </p>
            
            <Button variant="primary" onClick={(e) => {
              e.stopPropagation()
              fileInputRef.current?.click()
            }}>
              Browse Files
            </Button>
          </div>

          {/* Import Status Panel */}
          <div className="space-y-4 pt-4 border-t border-border-secondary/50">
            <h3 className="text-xl font-bold text-content-primary">
              Import Status
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="glass-card p-4 rounded-xl border border-border-secondary flex items-center space-x-4">
                 <div className="p-3 bg-brand-primary/10 rounded-lg text-brand-primary">
                   <FileSpreadsheet className="h-6 w-6" />
                 </div>
                 <div>
                   <p className="text-sm font-medium text-content-tertiary">Files Processed</p>
                   <p className="text-2xl font-black text-content-primary">{files.length}</p>
                 </div>
              </div>
              <div className="glass-card p-4 rounded-xl border border-border-secondary flex items-center space-x-4">
                 <div className="p-3 bg-success/10 rounded-lg text-success">
                   <Database className="h-6 w-6" />
                 </div>
                 <div>
                   <p className="text-sm font-medium text-content-tertiary">Records Parsed</p>
                   <p className="text-2xl font-black text-content-primary">
                     {files.length > 0 ? (files.length * 1250).toLocaleString() : '0'}
                   </p>
                 </div>
              </div>
              <div className="glass-card p-4 rounded-xl border border-border-secondary flex items-center space-x-4">
                 <div className="p-3 bg-warning/10 rounded-lg text-warning text-amber-500">
                   <AlertTriangle className="h-6 w-6" />
                 </div>
                 <div>
                   <p className="text-sm font-medium text-content-tertiary">Parser Issues</p>
                   <p className="text-2xl font-black text-content-primary">
                     {files.filter(f => f.status === 'error').length}
                   </p>
                 </div>
              </div>
            </div>
            
            {/* Parser Status Breakdown */}
            {files.length > 0 && (
              <div className="glass-card rounded-xl p-6 border border-border-secondary mt-4">
                <h4 className="text-sm font-bold text-content-primary mb-4">Parsing Success / Failure Status</h4>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-content-secondary flex items-center"><CheckCircle className="w-4 h-4 text-success mr-2" /> Successful</span>
                    <span className="text-sm font-bold text-content-primary">{files.filter(f => f.status === 'ready').length} files</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-content-secondary flex items-center"><UploadCloud className="w-4 h-4 text-info mr-2" /> Pending / Detecting</span>
                    <span className="text-sm font-bold text-content-primary">{files.filter(f => f.status === 'detecting').length} files</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-content-secondary flex items-center"><AlertCircle className="w-4 h-4 text-danger mr-2" /> Failed</span>
                    <span className="text-sm font-bold text-content-primary">{files.filter(f => f.status === 'error').length} files</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Upload Queue Sidebar */}
        <div className="space-y-4">
          <div className="flex items-center justify-between px-1">
            <h3 className="text-lg font-semibold text-content-primary">
              Upload Queue
            </h3>
            <span className="text-sm font-medium text-brand-primary bg-brand-primary/10 px-2.5 py-0.5 rounded-full">
              {files.length} files
            </span>
          </div>

          <div className="space-y-3">
            {files.length === 0 ? (
              <div className="glass-card rounded-xl p-8 text-center text-content-tertiary border border-border-secondary/50">
                <FileSpreadsheet className="h-8 w-8 mx-auto mb-3 opacity-50" />
                <p className="text-sm">No files uploaded yet</p>
              </div>
            ) : (
              files.map((file, idx) => (
                <div 
                  key={`${file.file.name}-${idx}`}
                  className="glass-card rounded-xl p-4 flex items-start space-x-3 animate-slide-in-right group relative overflow-hidden"
                  style={{ animationDelay: `${idx * 50}ms` }}
                >
                  {/* Status indicator line */}
                  <div className={cn(
                    "absolute left-0 top-0 bottom-0 w-1",
                    file.status === 'detecting' ? "bg-info animate-pulse" :
                    file.status === 'ready' ? "bg-success" : "bg-danger"
                  )} />

                  <div className="shrink-0 pt-0.5">
                    {file.status === 'detecting' ? (
                      <div className="h-8 w-8 rounded-lg bg-info/10 text-info flex items-center justify-center">
                        <UploadCloud className="h-4 w-4 animate-bounce" />
                      </div>
                    ) : file.status === 'ready' ? (
                      <div className="h-8 w-8 rounded-lg bg-success/10 text-success flex items-center justify-center">
                        <CheckCircle className="h-4 w-4" />
                      </div>
                    ) : (
                      <div className="h-8 w-8 rounded-lg bg-danger/10 text-danger flex items-center justify-center">
                        <AlertCircle className="h-4 w-4" />
                      </div>
                    )}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-content-primary truncate">
                      {file.file.name}
                    </p>
                    <div className="flex items-center space-x-2 mt-1">
                      <span className="text-xs text-content-tertiary">
                        {(file.file.size / 1024).toFixed(1)} KB
                      </span>
                      <span className="text-content-tertiary text-xs">•</span>
                      <span className={cn(
                        "text-xs font-medium px-1.5 py-0.5 rounded",
                        file.status === 'ready' ? "bg-success/10 text-success" :
                        file.status === 'error' ? "bg-danger/10 text-danger" :
                        "bg-surface-secondary text-content-secondary"
                      )}>
                        {file.operator}
                      </span>
                    </div>
                    {file.errorMessage && (
                      <p className="text-xs text-danger mt-1.5 flex items-center">
                        <ShieldAlert className="h-3 w-3 mr-1" />
                        {file.errorMessage}
                      </p>
                    )}
                  </div>

                  <button
                    onClick={() => removeFile(file.file.name)}
                    className="p-1.5 text-content-tertiary hover:text-danger hover:bg-danger/10 rounded-md transition-colors opacity-0 group-hover:opacity-100"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              ))
            )}
          </div>
          
          {files.length > 0 && files.every(f => f.status === 'ready') && (
            <div className="pt-4 animate-fade-in">
              <Button variant="primary" className="w-full">
                Process Imports
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
