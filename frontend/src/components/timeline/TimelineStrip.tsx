import { Clock, Filter, FileUp, RefreshCw, PhoneCall, MessageSquare, MapPin, CheckCircle } from 'lucide-react'
import { cn } from '@/lib/cn'
import { useTimelineFilterStore, ALL_CATEGORIES, type EventCategory } from '@/stores/timelineFilterStore'

export type TimelineEventType = 'movement' | 'connection' | 'disconnection' | 'alert' | 'system'

export interface TimelineEvent {
  id: string
  timestamp: string
  title: string
  description: string
  type: TimelineEventType
  category?: EventCategory
  coordinates?: [number, number]
}

interface TimelineStripProps {
  events: TimelineEvent[]
  className?: string
  onEventClick?: (event: TimelineEvent) => void
}

export const getEventCategory = (event: TimelineEvent): EventCategory => {
  if (event.category) return event.category
  
  const titleLower = event.title.toLowerCase()
  const descLower = event.description.toLowerCase()
  
  if (titleLower.includes('import') || descLower.includes('import')) return 'Import'
  if (titleLower.includes('validation') || titleLower.includes('validate') || descLower.includes('validation')) return 'Validation'
  if (event.type === 'movement' || titleLower.includes('moved') || titleLower.includes('location')) return 'Movement'
  if (titleLower.includes('call') || descLower.includes('call') || titleLower.includes('online')) return 'Calls'
  if (titleLower.includes('sms') || descLower.includes('sms')) return 'SMS'
  
  return 'Normalization'
}

export const getCategoryIcon = (category: EventCategory) => {
  switch (category) {
    case 'Import': return <FileUp className="w-4 h-4" />
    case 'Normalization': return <RefreshCw className="w-4 h-4" />
    case 'Calls': return <PhoneCall className="w-4 h-4" />
    case 'SMS': return <MessageSquare className="w-4 h-4" />
    case 'Movement': return <MapPin className="w-4 h-4" />
    case 'Validation': return <CheckCircle className="w-4 h-4" />
  }
}

export const getCategoryColorClass = (category: EventCategory) => {
  switch (category) {
    case 'Import': return 'bg-blue-500/10 border-blue-500/20 text-blue-500'
    case 'Normalization': return 'bg-purple-500/10 border-purple-500/20 text-purple-500'
    case 'Calls': return 'bg-emerald-500/10 border-emerald-500/20 text-emerald-500'
    case 'SMS': return 'bg-teal-500/10 border-teal-500/20 text-teal-500'
    case 'Movement': return 'bg-amber-500/10 border-amber-500/20 text-amber-500'
    case 'Validation': return 'bg-indigo-500/10 border-indigo-500/20 text-indigo-500'
  }
}

export function TimelineStrip({ events, className, onEventClick }: TimelineStripProps) {
  const { selectedCategories, toggleCategory } = useTimelineFilterStore()

  // Calculate counts for each category based on the original events list
  const categoryCounts = (events || []).reduce((acc, event) => {
    const cat = getEventCategory(event)
    acc[cat] = (acc[cat] || 0) + 1
    return acc
  }, {} as Record<EventCategory, number>)

  // Filter events based on active checkboxes
  const filteredEvents = (events || []).filter(event => 
    selectedCategories.includes(getEventCategory(event))
  )

  return (
    <div className="w-full flex flex-col">
      {/* Timeline Controls Header */}
      <div className="px-4 py-3 border-b border-border-primary bg-surface-secondary/20 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-content-tertiary" />
          <span className="text-xs font-semibold text-content-secondary uppercase tracking-wider">Timeline Filters</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {ALL_CATEGORIES.map((cat) => {
            const isChecked = selectedCategories.includes(cat)
            const count = categoryCounts[cat] || 0
            const colorClass = getCategoryColorClass(cat)
            
            return (
              <label
                key={cat}
                className={cn(
                  "flex items-center gap-2 px-3 py-1.5 rounded-xl border text-xs font-semibold cursor-pointer transition-all duration-200 select-none",
                  isChecked 
                    ? `${colorClass} ring-1 ring-offset-0 ring-current border-current`
                    : "bg-surface-primary border-border-secondary text-content-tertiary hover:bg-surface-secondary"
                )}
              >
                <input
                  type="checkbox"
                  checked={isChecked}
                  onChange={() => toggleCategory(cat)}
                  className="sr-only"
                />
                {getCategoryIcon(cat)}
                <span>{cat}</span>
                <span className="px-1.5 py-0.2 text-[10px] rounded-md bg-black/10 dark:bg-white/10 opacity-80">{count}</span>
              </label>
            )
          })}
        </div>
      </div>

      {/* Timeline Scroll Area */}
      <div className={cn("w-full overflow-x-auto pb-4 custom-scrollbar", className)}>
        {filteredEvents.length === 0 ? (
          <div className="w-full p-8 flex flex-col items-center justify-center text-content-tertiary border border-dashed border-border-primary rounded-xl bg-surface-secondary/20 my-4">
            <Clock className="w-8 h-8 mb-3 opacity-50" />
            <p className="text-sm">No timeline events match the selected filters.</p>
          </div>
        ) : (
          <div className="flex items-start gap-0 min-w-max px-4 pt-4">
            {filteredEvents.map((event, index) => {
              const category = getEventCategory(event)
              const colorClass = getCategoryColorClass(category)
              
              return (
                <div 
                  key={event.id} 
                  className="flex flex-col relative group cursor-pointer w-72 shrink-0 pr-6"
                  onClick={() => onEventClick?.(event)}
                >
                  {/* Timeline Connecting Line */}
                  {index < filteredEvents.length - 1 && (
                    <div className="absolute top-5 left-10 right-6 h-[2px] bg-border-primary group-hover:bg-brand-primary/30 transition-colors z-0" />
                  )}
                  
                  {/* Event Node */}
                  <div className="relative z-10 flex items-center mb-4 gap-3">
                    <div className={cn(
                      "w-10 h-10 rounded-full border-2 flex items-center justify-center bg-surface-primary transition-all duration-300 group-hover:scale-110 group-hover:shadow-lg shadow-black/5",
                      colorClass
                    )}>
                      {getCategoryIcon(category)}
                    </div>
                    <div className="text-xs font-mono font-medium text-content-tertiary bg-surface-secondary/50 px-2.5 py-1 rounded-md border border-border-secondary">
                      {event.timestamp}
                    </div>
                  </div>
                  
                  {/* Content Card */}
                  <div className={cn(
                    "p-4 rounded-xl border border-border-secondary bg-surface-secondary/30 transition-all duration-300",
                    "group-hover:border-brand-primary/40 group-hover:bg-surface-secondary group-hover:shadow-lg group-hover:shadow-brand-primary/5",
                    "group-hover:-translate-y-1"
                  )}>
                    <div className="flex items-start justify-between gap-2 mb-1.5">
                      <h4 className="text-sm font-bold text-content-primary line-clamp-1">{event.title}</h4>
                    </div>
                    <p className="text-xs text-content-tertiary line-clamp-2 leading-relaxed">{event.description}</p>
                    
                    {event.coordinates && (
                      <div className="mt-3 flex items-center gap-1.5 text-[10px] font-mono text-content-tertiary bg-surface-primary px-2 py-1 rounded border border-border-primary inline-flex">
                        <MapPin className="w-3 h-3 text-brand-primary opacity-70" />
                        {event.coordinates[0].toFixed(4)}, {event.coordinates[1].toFixed(4)}
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
