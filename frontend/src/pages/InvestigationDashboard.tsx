import { useEffect, useState } from 'react'
import { MapPin, Search, Filter, Shield, AlertCircle, Signal, Clock, Loader2, Database } from 'lucide-react'
import { LeafletMap, type MapTower, type ConfidenceTier } from '@/components/map/LeafletMap'
import { TimelineStrip, getEventCategory, type TimelineEvent } from '@/components/timeline/TimelineStrip'
import { cn } from '@/lib/cn'
import { useTimelineFilterStore, type EventCategory } from '@/stores/timelineFilterStore'
import { caseService } from '@/services/case.service'
import { simulationService } from '@/services/simulationService'
import { api } from '@/lib/api'
import type { Case } from '@/types/case'



export default function InvestigationDashboard() {
  const [cases, setCases] = useState<Case[]>([])
  const [selectedCaseId, setSelectedCaseId] = useState<number | null>(null)
  const [selectedTowerId, setSelectedTowerId] = useState<string | null>(null)

  const [showHeatmap, setShowHeatmap] = useState(true)
  const [showPath, setShowPath] = useState(true)
  const [showCircles, setShowCircles] = useState(false)
  const [showMarkers, setShowMarkers] = useState(true)
  
  const [towers, setTowers] = useState<MapTower[]>([])
  const [events, setEvents] = useState<TimelineEvent[]>([])
  const [heatmapPoints, setHeatmapPoints] = useState<[number, number, number][]>([])
  
  const [isLoadingCases, setIsLoadingCases] = useState(true)
  const [isLoadingData, setIsLoadingData] = useState(false)
  
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
      // console.error('Failed to load cases:', err)
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
      const towersMap = new Map<string, MapTower>()
      
      try {
        const measurements = await simulationService.getMeasurements(caseCode)
        
        measurements.forEach((m: any) => {
          if (m.latitude != null && m.longitude != null) {
            const rssi = m.rssi_dbm ?? -80
            const confidenceTier: ConfidenceTier = 
              rssi >= -70 ? 'Known' : rssi >= -90 ? 'Estimated' : 'Unknown'
            
            // Cluster nearby pings (~10m grid) into distinct cell sites
            const syntheticId = `TWR-${m.latitude.toFixed(4)}-${m.longitude.toFixed(4)}`
            const towerId = m.tower_id || m.tower_code || syntheticId
            
            if (towersMap.has(towerId)) {
              const existing = towersMap.get(towerId)!
              ;(existing as any).pingCount = ((existing as any).pingCount || 1) + 1
            } else {
              towersMap.set(towerId, {
                id: towerId,
                name: m.tower_id ? `Tower ${m.tower_id}` : `Cell ${syntheticId}`,
                lat: m.latitude,
                lng: m.longitude,
                confidenceTier,
                radius_m: m.uncertainty_m || 1000,
                pingCount: 1
              } as any)
            }
          }
        })
        
        fetchedTowers = Array.from(towersMap.values())
      } catch (err) {
        // console.warn('Measurements could not be fetched for case:', err)
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
        
        const rawPoints = features
          .filter((f: any) => f?.geometry?.coordinates?.length >= 2)
          .map((f: any) => {
            const [lng, lat] = f.geometry.coordinates
            const intensity = f.properties?.intensity ?? 1.0
            return [lat, lng, intensity] as [number, number, number]
          })

        // Scale & normalize heatmap intensities so peak density glows vibrantly
        const maxIntensity = Math.max(...rawPoints.map((p: [number, number, number]) => p[2]), 0.0001)
        fetchedHeatmap = rawPoints.map(([lat, lng, int]: [number, number, number]) => [
          lat,
          lng,
          Math.min(1.0, Math.max(0.2, (int / maxIntensity) * 1.2))
        ])
      } catch (err) {
        // console.warn('Heatmap could not be fetched for case:', err)
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
              : `Location update. Speed: ${evt.speed_kmh != null ? evt.speed_kmh.toFixed(1) + ' km/h' : 'Unknown'}, Confidence: ${evt.confidence != null ? (evt.confidence * 100).toFixed(0) + '%' : 'Unknown'}`,
            type: evt.event_type === 'handover' ? 'connection' : 'movement',
            category,
            coordinates: (evt.latitude != null && evt.longitude != null) 
              ? [evt.latitude, evt.longitude] as [number, number] 
              : undefined
          }
        })
        
        // If there are no towers from measurements (real cases), cluster movement events into top 25 towers
        if (towersMap.size === 0 && rawEvents.length > 0) {
          const countsMap = new Map<string, { lat: number; lng: number; count: number }>()

          rawEvents.forEach((evt: any) => {
            if (evt.latitude != null && evt.longitude != null) {
              const clusterKey = `${evt.latitude.toFixed(3)},${evt.longitude.toFixed(3)}`
              const existing = countsMap.get(clusterKey)
              if (existing) {
                existing.count += 1
              } else {
                countsMap.set(clusterKey, { lat: evt.latitude, lng: evt.longitude, count: 1 })
              }
            }
          })

          // Sort by count descending & take top 25
          const sortedClusters = Array.from(countsMap.entries())
            .sort((a, b) => b[1].count - a[1].count)
            .slice(0, 25)

          sortedClusters.forEach(([key, val], idx) => {
            const syntheticId = `CELL-${key.replace(',', '-')}`
            const tier: ConfidenceTier = val.count >= 25 ? 'Known' : val.count >= 10 ? 'Estimated' : 'Unknown'
            towersMap.set(syntheticId, {
              id: syntheticId,
              name: `Tower Cell #${idx + 1} (${val.count} pings)`,
              lat: val.lat,
              lng: val.lng,
              confidenceTier: tier,
              radius_m: val.count >= 25 ? 300 : val.count >= 10 ? 600 : 1000
            })
          })

          fetchedTowers = Array.from(towersMap.values())
        }
      } catch (err) {
        // console.warn('Movement events could not be reconstructed for case:', err)
      }

      // Apply case data if we got anything valid
      setTowers(fetchedTowers)
      setHeatmapPoints(fetchedHeatmap)
      setEvents(fetchedEvents)
    } catch (err) {
      // console.error('Failed to load case details:', err)
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

  // Cap visible tower cards in DOM to top 100 for 60fps scrolling
  const visibleTowers = filteredTowers.slice(0, 100)

  // Calculate map center prioritizing towers, then heatmap, then default to Bangalore
  const centerLat = filteredTowers.length > 0 
    ? filteredTowers.reduce((acc, t) => acc + t.lat, 0) / filteredTowers.length 
    : heatmapPoints.length > 0 
      ? heatmapPoints.reduce((acc: number, pt: [number, number, number]) => acc + pt[0], 0) / heatmapPoints.length 
      : 12.9716

  const centerLng = filteredTowers.length > 0 
    ? filteredTowers.reduce((acc, t) => acc + t.lng, 0) / filteredTowers.length 
    : heatmapPoints.length > 0 
      ? heatmapPoints.reduce((acc: number, pt: [number, number, number]) => acc + pt[1], 0) / heatmapPoints.length 
      : 77.5946

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
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[560px] shrink-0">
            
            {/* Left Column: Tower Registry Explorer */}
            <div className="lg:col-span-1 bg-surface-primary border border-border-primary rounded-2xl flex flex-col overflow-hidden h-full">
              <div className="p-4 border-b border-border-primary bg-surface-secondary/50">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-lg font-bold text-content-primary flex items-center gap-2">
                    <Signal className="w-5 h-5 text-brand-primary" />
                    Tower Registry
                  </h2>
                  <span className="text-xs font-semibold text-content-tertiary bg-surface-primary px-2.5 py-1 rounded-full border border-border-secondary">
                    {visibleTowers.length} / {filteredTowers.length} Sites
                  </span>
                </div>
                
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
                {visibleTowers.length > 0 ? (
                  visibleTowers.map(tower => {
                    const isSelected = selectedTowerId === tower.id
                    const pings = (tower as any).pingCount
                    return (
                      <div 
                        key={tower.id} 
                        onClick={() => setSelectedTowerId(isSelected ? null : tower.id)}
                        className={cn(
                          "p-4 rounded-xl border transition-all cursor-pointer",
                          isSelected 
                            ? "bg-brand-primary/10 border-brand-primary ring-1 ring-brand-primary/50 shadow-md" 
                            : "bg-surface-secondary/30 border-border-secondary hover:border-brand-primary/30"
                        )}
                      >
                        <div className="flex justify-between items-start mb-2">
                          <h3 className="font-bold text-sm text-content-primary">{tower.name}</h3>
                          <TierBadge tier={tower.confidenceTier} />
                        </div>
                        <div className="flex justify-between items-center text-xs text-content-tertiary font-mono mb-2">
                          <span>{tower.id}</span>
                          {pings && (
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-brand-primary/10 text-brand-primary border border-brand-primary/20">
                              {pings} pings
                            </span>
                          )}
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
                    )
                  })
                ) : (
                  <div className="text-center p-8 text-content-tertiary text-sm">
                    No towers found matching criteria.
                  </div>
                )}
              </div>
            </div>

            {/* Right Column: Map */}
            <div className="lg:col-span-2 bg-surface-primary border border-border-primary rounded-2xl flex flex-col overflow-hidden relative min-h-[400px]">
              <div className="p-4 border-b border-border-primary bg-surface-secondary/50 flex flex-wrap justify-between items-center absolute top-0 left-0 right-0 z-10 backdrop-blur-md bg-surface-primary/80 gap-2">
                <h2 className="text-lg font-bold text-content-primary flex items-center gap-2">
                  <MapPin className="w-5 h-5 text-brand-primary" />
                  Geospatial View
                </h2>
                
                {/* Interactive Layer Toggles */}
                <div className="flex items-center gap-1.5 bg-surface-secondary/80 p-1 rounded-xl border border-border-secondary">
                  <button
                    onClick={() => setShowHeatmap(!showHeatmap)}
                    className={cn(
                      "px-2.5 py-1 text-xs font-bold rounded-lg transition-all flex items-center gap-1 cursor-pointer",
                      showHeatmap 
                        ? "bg-rose-500/20 text-rose-500 border border-rose-500/40 shadow-sm" 
                        : "text-content-tertiary hover:text-content-primary opacity-60"
                    )}
                  >
                    🔥 Heatmap
                  </button>

                  <button
                    onClick={() => setShowPath(!showPath)}
                    className={cn(
                      "px-2.5 py-1 text-xs font-bold rounded-lg transition-all flex items-center gap-1 cursor-pointer",
                      showPath 
                        ? "bg-indigo-500/20 text-indigo-500 border border-indigo-500/40 shadow-sm" 
                        : "text-content-tertiary hover:text-content-primary opacity-60"
                    )}
                  >
                    🔵 Path
                  </button>

                  <button
                    onClick={() => setShowCircles(!showCircles)}
                    className={cn(
                      "px-2.5 py-1 text-xs font-bold rounded-lg transition-all flex items-center gap-1 cursor-pointer",
                      showCircles 
                        ? "bg-amber-500/20 text-amber-500 border border-amber-500/40 shadow-sm" 
                        : "text-content-tertiary hover:text-content-primary opacity-60"
                    )}
                  >
                    ⭕ Circles
                  </button>

                  <button
                    onClick={() => setShowMarkers(!showMarkers)}
                    className={cn(
                      "px-2.5 py-1 text-xs font-bold rounded-lg transition-all flex items-center gap-1 cursor-pointer",
                      showMarkers 
                        ? "bg-emerald-500/20 text-emerald-500 border border-emerald-500/40 shadow-sm" 
                        : "text-content-tertiary hover:text-content-primary opacity-60"
                    )}
                  >
                    📍 Towers
                  </button>
                </div>
              </div>

              <div className="flex-1 w-full h-full pt-16">
                <LeafletMap 
                  towers={filteredTowers}
                  selectedTowerId={selectedTowerId}
                  onSelectTower={setSelectedTowerId}
                  center={[centerLat, centerLng]}
                  zoom={13}
                  pathCoordinates={pathCoordinates}
                  heatmapPoints={heatmapPoints}
                  showHeatmap={showHeatmap}
                  showPath={showPath}
                  showCircles={showCircles}
                  showMarkers={showMarkers}
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
