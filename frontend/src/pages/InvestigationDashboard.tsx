import { useEffect, useState } from 'react'
import { MapPin, Search, Filter, Shield, AlertCircle, Signal } from 'lucide-react'
import { LeafletMap, type MapTower, type ConfidenceTier } from '@/components/map/LeafletMap'
import { cn } from '@/lib/cn'

// Mock Data for the Tower Registry
const MOCK_TOWERS: MapTower[] = [
  { id: 'TWR-101', name: 'Alpha Station', lat: 12.9716, lng: 77.5946, confidenceTier: 'Known', radius_m: 1500 },
  { id: 'TWR-102', name: 'Beta Sector', lat: 12.9750, lng: 77.5900, confidenceTier: 'Known', radius_m: 1200 },
  { id: 'TWR-103', name: 'Gamma Relay', lat: 12.9680, lng: 77.5850, confidenceTier: 'Estimated', radius_m: 2000 },
  { id: 'TWR-104', name: 'Delta Node', lat: 12.9650, lng: 77.6050, confidenceTier: 'Unknown', radius_m: 800 },
  { id: 'TWR-105', name: 'Epsilon Mast', lat: 12.9800, lng: 77.6000, confidenceTier: 'Estimated', radius_m: 1800 },
]

export default function InvestigationDashboard() {
  const [searchTerm, setSearchTerm] = useState('')
  const [filterTier, setFilterTier] = useState<ConfidenceTier | 'All'>('All')

  useEffect(() => {
    document.title = 'Investigation Dashboard — Asterion'
  }, [])

  const filteredTowers = MOCK_TOWERS.filter(t => {
    const matchesSearch = t.name?.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          t.id.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesTier = filterTier === 'All' || t.confidenceTier === filterTier
    return matchesSearch && matchesTier
  })

  // Calculate center of map based on filtered towers
  const centerLat = filteredTowers.length > 0 ? filteredTowers.reduce((acc, t) => acc + t.lat, 0) / filteredTowers.length : 12.9716
  const centerLng = filteredTowers.length > 0 ? filteredTowers.reduce((acc, t) => acc + t.lng, 0) / filteredTowers.length : 77.5946

  return (
    <div className="space-y-6 animate-fade-in pb-12 h-[calc(100vh-80px)] flex flex-col">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-border-primary pb-5 shrink-0">
        <div>
          <h1 className="text-3xl font-extrabold text-content-primary tracking-tight flex items-center space-x-3">
            <MapPin className="h-8 w-8 text-brand-secondary" />
            <span>Investigation Dashboard</span>
          </h1>
          <p className="text-sm text-content-tertiary mt-2">
            Tower Registry Explorer and Map Visualization
          </p>
        </div>
      </div>

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
            />
          </div>
        </div>

      </div>
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
