import { useEffect, useState } from 'react'
import { MapPin, Search, Filter, Shield, AlertCircle, Signal, Clock, Loader2, Database, AlertTriangle } from 'lucide-react'
import { LeafletMap, type MapTower, type ConfidenceTier } from '@/components/map/LeafletMap'
import { TimelineStrip, getEventCategory, type TimelineEvent } from '@/components/timeline/TimelineStrip'
import { cn } from '@/lib/cn'
import { useTimelineFilterStore, type EventCategory } from '@/stores/timelineFilterStore'
import { caseService } from '@/services/case.service'
import { simulationService } from '@/services/simulationService'
import { api } from '@/lib/api'
import type { Case } from '@/types/case'

// Fallback Mock Data in case backend has no data or is loading
const MOCK_TOWERS: MapTower[] = [
  { id: 'TWR-101', name: 'Alpha Station', lat: 12.9716, lng: 77.5946, confidenceTier: 'Known', radius_m: 1500 },
  { id: 'TWR-102', name: 'Beta Sector', lat: 12.9750, lng: 77.5900, confidenceTier: 'Known', radius_m: 1200 },
  { id: 'TWR-103', name: 'Gamma Relay', lat: 12.9680, lng: 77.5850, confidenceTier: 'Estimated', radius_m: 2000 },
  { id: 'TWR-104', name: 'Delta Node', lat: 12.9650, lng: 77.6050, confidenceTier: 'Unknown', radius_m: 800 },
  { id: 'TWR-105', name: 'Epsilon Mast', lat: 12.9800, lng: 77.6000, confidenceTier: 'Estimated', radius_m: 1800 },
]

const MOCK_EVENTS: TimelineEvent[] = [
  { id: 'ev-1', timestamp: '08:00 AM', title: 'Device Online', description: 'Initial connection to network.', type: 'connection', category: 'Calls' },
  { id: 'ev-2', timestamp: '08:15 AM', title: 'Location Update', description: 'Device connected to Alpha Station.', type: 'movement', category: 'Movement', coordinates: [12.9716, 77.5946] },
  { id: 'ev-3', timestamp: '09:30 AM', title: 'Location Update', description: 'Device moved to Beta Sector.', type: 'movement', category: 'Movement', coordinates: [12.9750, 77.5900] },
  { id: 'ev-4', timestamp: '10:45 AM', title: 'Signal Drop', description: 'Lost connection briefly.', type: 'alert', category: 'Normalization' },
  { id: 'ev-5', timestamp: '11:00 AM', title: 'Location Update', description: 'Device detected at Delta Node.', type: 'movement', category: 'Movement', coordinates: [12.9650, 77.6050] },
  { id: 'ev-6', timestamp: '12:30 PM', title: 'System Check', description: 'Automated diagnostic complete.', type: 'system', category: 'Validation' }
]

const MOCK_HEATMAP: [number, number, number][] = [
  [12.9716, 77.5946, 0.9],
  [12.9750, 77.5900, 0.7],
  [12.9680, 77.5850, 0.5],
  [12.9650, 77.6050, 0.8],
  [12.9800, 77.6000, 0.4]
]

export default function InvestigationDashboard() {
  const [cases, setCases] = useState<Case[]>([])
  const [selectedCaseId, setSelectedCaseId] = useState<number | null>(null)
  
  const [towers, setTowers] = useState<MapTower[]>(MOCK_TOWERS)
  const [events, setEvents] = useState<TimelineEvent[]>(MOCK_EVENTS)
  const [heatmapPoints, setHeatmapPoints] = useState<[number, number, number][]>(MOCK_HEATMAP)
  
  const [isLoadingCases, setIsLoadingCases] = useState(true)
  const [isLoadingData, setIsLoadingData] = useState(false)
  const [isUsingMockData, setIsUsingMockData] = useState(true)
  
  const [searchTerm, setSearchTerm] = useState('')
  const [filterTier, setFilterTier] = useState<ConfidenceTier | 'All'>('All')
  
  const { selectedCategories } = useTimelineFilterStore()

  useEffect(() => {
    document.title = 'Investigation Dashboard — Asterion'
    loadCases()
  }, [])

  const loadCases = async () => {
    try {
      setIsLoadingCases(true)
      const list = await caseService.getCases()
      setCases(list)
      if (list.length > 0) {
        setSelectedCaseId(list[0].id)
      }
    } catch (err) {
      console.error('Failed to load cases:', err)
    } finally {
      setIsLoadingCases(false)
    }
  }

  // Load heatmap, towers and events for selected case
  useEffect(() => {
    if (selectedCaseId === null) return
    loadCaseData(selectedCaseId)
  }, [selectedCaseId])

  const loadCaseData = async (caseId: number) => {
    try {
      setIsLoadingData(true)
      const caseCode = `CASE-${String(caseId).padStart(3, '0')}`

      // 1. Fetch case towers via measurements
      let fetchedTowers: MapTower[] = []
      try {
        const measurements = await simulationService.getMeasurements(caseCode)
        const towersMap = new Map<string, MapTower>()
        
        measurements.forEach((m: any) => {
          if (m.latitude != null && m.longitude != null) {
            const rssi = m.rssi_dbm ?? -80
            const confidenceTier: ConfidenceTier = 
              rssi >= -70 ? 'Known' : rssi >= -90 ? 'Estimated' : 'Unknown'
            
            towersMap.set(m.tower_id || 'UNKNOWN', {
              id: m.tower_id || 'UNKNOWN',
              name: `Tower ${m.tower_id}`,
              lat: m.latitude,
              lng: m.longitude,
              confidenceTier,
              radius_m: m.uncertainty_m || 1000
            })
          }
        })
        
        fetchedTowers = Array.from(towersMap.values())
      } catch (err) {
        console.warn('Measurements could not be fetched for case:', err)
      }

      // 2. Fetch Heatmap points
      let fetchedHeatmap: [number, number, number][] = []
      try {
        const heatmapRes = await api.get(`/dashboard/${caseId}/heatmap`)
        // After APIResponse unwrapping, heatmapRes.data is the FeatureCollection dict
        const payload = heatmapRes.data
        const features = Array.isArray(payload?.features)
          ? payload.features
          : Array.isArray((payload as any)?.data?.features)
            ? (payload as any).data.features
            : []
        
        fetchedHeatmap = features
          .filter((f: any) => f?.geometry?.coordinates?.length >= 2)
          .map((f: any) => {
            const [lng, lat] = f.geometry.coordinates
            const intensity = f.properties?.intensity ?? 1.0
            return [lat, lng, intensity] as [number, number, number]
          })
      } catch (err) {
        console.warn('Heatmap could not be fetched for case:', err)
      }

      // 3. Fetch movement events (Timeline)
      let fetchedEvents: TimelineEvent[] = []
      try {
        const reconRes = await api.post(`/movement/reconstruct?case_code=${caseCode}`)
        const rawEvents = reconRes.data?.events || reconRes.data?.data?.events || []
        
        fetchedEvents = rawEvents.map((evt: any, idx: number) => {
          let category: EventCategory = 'Movement'
          if (evt.event_type === 'call_start' || evt.event_type === 'call_end') {
            category = 'Calls'
          } else if (evt.event_type === 'sms') {
            category = 'SMS'
          } else if (evt.event_type === 'import') {
            category = 'Import'
          } else if (evt.event_type === 'validation') {
            category = 'Validation'
          } else if (evt.event_type === 'normalization') {
            category = 'Normalization'
          }

          return {
            id: `evt-${idx}-${evt.sequence_number}`,
            timestamp: evt.timestamp 
              ? new Date(evt.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) 
              : '—',
            title: evt.event_type.replace(/_/g, ' ').toUpperCase(),
            description: evt.event_type === 'handover' 
              ? `Handover from ${evt.from_cgi || '—'} to ${evt.to_cgi || '—'}`
              : `Location update. Speed: ${evt.speed_kmh?.toFixed(1) || 0} km/h, Confidence: ${(evt.confidence * 100)?.toFixed(0) || 100}%`,
            type: evt.event_type === 'handover' ? 'connection' : 'movement',
            category,
            coordinates: (evt.latitude != null && evt.longitude != null) 
              ? [evt.latitude, evt.longitude] as [number, number] 
              : undefined
          }
        })
      } catch (err) {
        console.warn('Movement events could not be reconstructed for case:', err)
      }

      // Apply case data if we got anything valid
      if (fetchedTowers.length > 0 || fetchedHeatmap.length > 0 || fetchedEvents.length > 0) {
        setTowers(fetchedTowers.length > 0 ? fetchedTowers : MOCK_TOWERS)
        setHeatmapPoints(fetchedHeatmap.length > 0 ? fetchedHeatmap : MOCK_HEATMAP)
        setEvents(fetchedEvents.length > 0 ? fetchedEvents : MOCK_EVENTS)
        setIsUsingMockData(false)
      } else {
        // Use Mock data as fallback
        setTowers(MOCK_TOWERS)
        setHeatmapPoints(MOCK_HEATMAP)
        setEvents(MOCK_EVENTS)
        setIsUsingMockData(true)
      }
    } catch (err) {
      console.error('Failed to load case details:', err)
      setIsUsingMockData(true)
    } finally {
      setIsLoadingData(false)
    }
  }

  // Filter towers based on search term and confidence tier
  const filteredTowers = towers.filter(t => {
    const matchesSearch = t.name?.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          t.id.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesTier = filterTier === 'All' || t.confidenceTier === filterTier
    return matchesSearch && matchesTier
  })

  // Calculate center of map based on filtered towers
  const centerLat = filteredTowers.length > 0 ? filteredTowers.reduce((acc, t) => acc + t.lat, 0) / filteredTowers.length : 12.9716
  const centerLng = filteredTowers.length > 0 ? filteredTowers.reduce((acc, t) => acc + t.lng, 0) / filteredTowers.length : 77.5946

  // Filter events by the selected checkboxes in the Zustand store
  const filteredEvents = events.filter(e => selectedCategories.includes(getEventCategory(e)))

  // Filter map path coordinates based on the filtered timeline events
  const pathCoordinates = filteredEvents
    .filter(e => e.coordinates)
    .map(e => e.coordinates as [number, number])

  return (
    <div className="space-y-6 animate-fade-in pb-12 min-h-[calc(100vh-80px)] flex flex-col">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-border-primary pb-5 shrink-0">
        <div>
          <h1 className="text-3xl font-extrabold text-content-primary tracking-tight flex items-center space-x-3">
            <MapPin className="h-8 w-8 text-brand-secondary" />
            <span>Investigation Dashboard</span>
          </h1>
          <p className="text-sm text-content-tertiary mt-2">
            Geospatial Analysis, Event Filtering, and Density Heatmap
          </p>
        </div>

        {/* Case Selector Dropdown */}
        <div className="flex items-center gap-3 bg-surface-secondary/40 p-2 rounded-xl border border-border-primary">
          <Database className="w-4 h-4 text-brand-primary" />
          <span className="text-xs font-semibold text-content-secondary uppercase tracking-wider">Case:</span>
          {isLoadingCases ? (
            <Loader2 className="w-4 h-4 animate-spin text-brand-primary" />
          ) : (
            <select
              value={selectedCaseId || ''}
              onChange={(e) => setSelectedCaseId(Number(e.target.value))}
              className="bg-surface-primary border border-border-secondary text-content-primary text-xs font-bold rounded-lg px-3 py-1.5 focus:outline-none focus:border-brand-primary cursor-pointer max-w-[200px] truncate"
            >
              {cases.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.title}
                </option>
              ))}
              {cases.length === 0 && <option value="">No Cases Seeded</option>}
            </select>
          )}

          {isUsingMockData && (
            <span className="flex items-center gap-1 text-[10px] font-bold text-amber-500 bg-amber-500/10 border border-amber-500/20 px-2 py-1 rounded-md uppercase">
              <AlertTriangle className="w-3 h-3" /> DEMO MODE
            </span>
          )}
        </div>
      </div>

      {isLoadingData ? (
        <div className="flex-1 flex flex-col items-center justify-center text-content-secondary">
          <Loader2 className="w-10 h-10 animate-spin text-brand-primary mb-3" />
          <span className="text-sm font-medium">Reconstructing movement events and loading heatmap...</span>
        </div>
      ) : (
        <>
          {/* Main Content Area */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1 min-h-0">
            
            {/* Left Column: Tower Registry Explorer */}
            <div className="lg:col-span-1 bg-surface-primary border border-border-primary rounded-2xl flex flex-col overflow-hidden">
              <div className="p-4 border-b border-border-primary bg-surface-secondary/50">
                <h2 className="text-lg font-bold text-content-primary mb-4 flex items-center gap-2">
                  <Signal className="w-5 h-5 text-brand-primary" />
                  Tower Registry
                </h2>
                
                <div className="space-y-3">
                  {/* Search */}
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-content-tertiary" />
                    <input 
                      type="text" 
                      placeholder="Search towers..." 
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="w-full bg-surface-primary border border-border-primary rounded-xl pl-9 pr-4 py-2 text-sm text-content-primary focus:outline-none focus:border-brand-primary transition-colors"
                    />
                  </div>
                  
                  {/* Filters */}
                  <div className="flex items-center gap-2">
                    <Filter className="w-4 h-4 text-content-tertiary" />
                    <div className="flex gap-2">
                      {(['All', 'Known', 'Estimated', 'Unknown'] as const).map(tier => (
                        <button
                          key={tier}
                          onClick={() => setFilterTier(tier)}
                          className={cn(
                            "px-3 py-1 text-xs font-semibold rounded-full border transition-colors",
                            filterTier === tier 
                              ? "bg-brand-primary/20 border-brand-primary text-brand-primary"
                              : "bg-surface-primary border-border-secondary text-content-tertiary hover:bg-surface-secondary"
                          )}
                        >
                          {tier}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Tower List */}
              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {filteredTowers.length > 0 ? (
                  filteredTowers.map(tower => (
                    <div key={tower.id} className="p-4 rounded-xl border border-border-secondary bg-surface-secondary/30 hover:border-brand-primary/30 transition-colors">
                      <div className="flex justify-between items-start mb-2">
                        <h3 className="font-bold text-sm text-content-primary">{tower.name}</h3>
                        <TierBadge tier={tower.confidenceTier} />
                      </div>
                      <div className="text-xs text-content-tertiary font-mono mb-2">
                        {tower.id}
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-xs text-content-secondary mt-3 bg-surface-primary p-2 rounded-lg border border-border-primary">
                        <div>
                          <span className="text-content-tertiary block mb-0.5">Lat</span>
                          <span className="font-mono">{tower.lat.toFixed(4)}</span>
                        </div>
                        <div>
                          <span className="text-content-tertiary block mb-0.5">Lng</span>
                          <span className="font-mono">{tower.lng.toFixed(4)}</span>
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center p-8 text-content-tertiary text-sm">
                    No towers found matching criteria.
                  </div>
                )}
              </div>
            </div>

            {/* Right Column: Map */}
            <div className="lg:col-span-2 bg-surface-primary border border-border-primary rounded-2xl flex flex-col overflow-hidden relative min-h-[400px]">
              <div className="p-4 border-b border-border-primary bg-surface-secondary/50 flex justify-between items-center absolute top-0 left-0 right-0 z-10 backdrop-blur-md bg-surface-primary/80">
                <h2 className="text-lg font-bold text-content-primary flex items-center gap-2">
                  <MapPin className="w-5 h-5 text-brand-primary" />
                  Geospatial View
                </h2>
                <div className="flex gap-4 text-xs font-medium bg-surface-secondary px-3 py-1.5 rounded-lg border border-border-secondary">
                  <div className="flex items-center gap-1.5"><div className="w-2.5 h-2.5 rounded-full bg-emerald-500"></div>Known</div>
                  <div className="flex items-center gap-1.5"><div className="w-2.5 h-2.5 rounded-full bg-amber-500"></div>Estimated</div>
                  <div className="flex items-center gap-1.5"><div className="w-2.5 h-2.5 rounded-full bg-red-500"></div>Unknown</div>
                </div>
              </div>
              <div className="flex-1 w-full h-full pt-16">
                <LeafletMap 
                  towers={filteredTowers}
                  center={[centerLat, centerLng]}
                  zoom={13}
                  pathCoordinates={pathCoordinates}
                  heatmapPoints={heatmapPoints}
                />
              </div>
            </div>

          </div>

          {/* Bottom Row: Timeline Strip */}
          <div className="bg-surface-primary border border-border-primary rounded-2xl flex flex-col overflow-hidden shrink-0">
            <div className="p-4 border-b border-border-primary bg-surface-secondary/50">
              <h2 className="text-lg font-bold text-content-primary flex items-center gap-2">
                <Clock className="w-5 h-5 text-brand-primary" />
                Movement Timeline
              </h2>
            </div>
            <div className="p-2">
              <TimelineStrip events={events} />
            </div>
          </div>
        </>
      )}
    </div>
  )
}

function TierBadge({ tier }: { tier: ConfidenceTier }) {
  if (tier === 'Known') {
    return <span className="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-bold rounded-md bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 uppercase tracking-wide"><Shield className="w-3 h-3" /> {tier}</span>
  }
  if (tier === 'Estimated') {
    return <span className="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-bold rounded-md bg-amber-500/10 text-amber-500 border border-amber-500/20 uppercase tracking-wide"><AlertCircle className="w-3 h-3" /> {tier}</span>
  }
  return <span className="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-bold rounded-md bg-red-500/10 text-red-500 border border-red-500/20 uppercase tracking-wide"><AlertCircle className="w-3 h-3" /> {tier}</span>
}
