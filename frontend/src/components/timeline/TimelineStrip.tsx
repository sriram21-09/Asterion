import React from 'react'
import { Clock, Activity, Signal, AlertTriangle, ShieldCheck, MapPin } from 'lucide-react'
import { cn } from '@/lib/cn'

export type TimelineEventType = 'movement' | 'connection' | 'disconnection' | 'alert' | 'system'

export interface TimelineEvent {
  id: string
  timestamp: string
  title: string
  description: string
  type: TimelineEventType
  coordinates?: [number, number]
}

interface TimelineStripProps {
  events: TimelineEvent[]
  className?: string
  onEventClick?: (event: TimelineEvent) => void
}

const getEventIcon = (type: TimelineEventType) => {
  switch (type) {
    case 'movement': return <MapPin className="w-4 h-4 text-brand-primary" />
    case 'connection': return <Signal className="w-4 h-4 text-emerald-500" />
    case 'disconnection': return <Activity className="w-4 h-4 text-amber-500" />
    case 'alert': return <AlertTriangle className="w-4 h-4 text-red-500" />
    case 'system': return <ShieldCheck className="w-4 h-4 text-indigo-500" />
    default: return <Clock className="w-4 h-4 text-content-tertiary" />
  }
}

const getEventColor = (type: TimelineEventType) => {
  switch (type) {
    case 'movement': return 'bg-brand-primary/10 border-brand-primary/20 text-brand-primary'
    case 'connection': return 'bg-emerald-500/10 border-emerald-500/20 text-emerald-500'
    case 'disconnection': return 'bg-amber-500/10 border-amber-500/20 text-amber-500'
    case 'alert': return 'bg-red-500/10 border-red-500/20 text-red-500'
    case 'system': return 'bg-indigo-500/10 border-indigo-500/20 text-indigo-500'
    default: return 'bg-surface-secondary border-border-secondary text-content-tertiary'
  }
}

export function TimelineStrip({ events, className, onEventClick }: TimelineStripProps) {
  if (!events || events.length === 0) {
    return (
      <div className="w-full p-8 flex flex-col items-center justify-center text-content-tertiary border border-dashed border-border-primary rounded-xl bg-surface-secondary/20">
        <Clock className="w-8 h-8 mb-3 opacity-50" />
        <p className="text-sm">No timeline events recorded.</p>
      </div>
    )
  }

  return (
    <div className={cn("w-full overflow-x-auto pb-4 custom-scrollbar", className)}>
      <div className="flex items-start gap-0 min-w-max px-4 pt-4">
        {events.map((event, index) => (
          <div 
            key={event.id} 
            className="flex flex-col relative group cursor-pointer w-72 shrink-0 pr-6"
            onClick={() => onEventClick?.(event)}
          >
            {/* Timeline Connecting Line */}
            {index < events.length - 1 && (
              <div className="absolute top-5 left-10 right-6 h-[2px] bg-border-primary group-hover:bg-brand-primary/30 transition-colors z-0" />
            )}
            
            {/* Event Node */}
            <div className="relative z-10 flex items-center mb-4 gap-3">
              <div className={cn(
                "w-10 h-10 rounded-full border-2 flex items-center justify-center bg-surface-primary transition-all duration-300 group-hover:scale-110 group-hover:shadow-lg shadow-black/5",
                getEventColor(event.type)
              )}>
                {getEventIcon(event.type)}
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
        ))}
      </div>
    </div>
  )
}
