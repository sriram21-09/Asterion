import { useEffect, useMemo } from 'react'
import { MapContainer, TileLayer, Marker, Popup, useMap, Polyline, LayerGroup, Circle } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import 'leaflet.markercluster/dist/MarkerCluster.css'
import 'leaflet.markercluster/dist/MarkerCluster.Default.css'
import { HeatmapLayer } from './HeatmapLayer'
import MarkerClusterGroup from 'react-leaflet-cluster'
import { useThemeStore } from '@/stores/useThemeStore'

export type ConfidenceTier = 'Known' | 'Estimated' | 'Unknown'

export interface MapTower {
  id: string
  name?: string
  lat: number
  lng: number
  confidenceTier: ConfidenceTier
  radius_m?: number
}

interface LeafletMapProps {
  towers: MapTower[]
  selectedTowerId?: string | null
  onSelectTower?: (id: string) => void
  center?: [number, number]
  zoom?: number
  pathCoordinates?: [number, number][]
  heatmapPoints?: [number, number, number][]
  showHeatmap?: boolean
  showPath?: boolean
  showCircles?: boolean
  showMarkers?: boolean
}

const createCustomIcon = (color: string, isSelected: boolean = false) => {
  const size = isSelected ? 22 : 16
  const border = isSelected ? '3px solid #6366f1' : '2px solid white'
  const shadow = isSelected ? '0 0 12px #6366f1' : '0 0 4px rgba(0,0,0,0.5)'
  return L.divIcon({
    className: 'custom-leaflet-marker',
    html: `
      <div style="
        background-color: ${color};
        width: ${size}px;
        height: ${size}px;
        border-radius: 50%;
        border: ${border};
        box-shadow: ${shadow};
        transition: all 0.2s ease;
      "></div>
    `,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -size / 2],
  })
}

const ICONS = {
  Known: (selected = false) => createCustomIcon('#10b981', selected),
  Estimated: (selected = false) => createCustomIcon('#f59e0b', selected),
  Unknown: (selected = false) => createCustomIcon('#ef4444', selected),
}

function MapUpdater({ 
  center, 
  zoom, 
  towers, 
  pathCoordinates, 
  heatmapPoints 
}: { 
  center: [number, number]
  zoom: number
  towers: MapTower[]
  pathCoordinates?: [number, number][]
  heatmapPoints?: [number, number, number][]
}) {
  const map = useMap()

  useEffect(() => {
    const points: [number, number][] = []
    
    if (towers && towers.length > 0) {
      towers.forEach(t => points.push([t.lat, t.lng]))
    }
    if (pathCoordinates && pathCoordinates.length > 0) {
      pathCoordinates.forEach(p => points.push(p))
    }
    if (heatmapPoints && heatmapPoints.length > 0) {
      heatmapPoints.forEach(h => points.push([h[0], h[1]]))
    }

    if (points.length > 0) {
      const bounds = L.latLngBounds(points)
      if (bounds.isValid()) {
        map.fitBounds(bounds, { padding: [40, 40], maxZoom: 15, animate: true })
        return
      }
    }

    map.setView(center, zoom)
  }, [center, zoom, towers, pathCoordinates, heatmapPoints, map])

  return null
}

export function LeafletMap({ 
  towers, 
  selectedTowerId,
  onSelectTower,
  center = [12.9716, 77.5946], 
  zoom = 13, 
  pathCoordinates, 
  heatmapPoints,
  showHeatmap = true,
  showPath = true,
  showCircles = false,
  showMarkers = true
}: LeafletMapProps) {
  const { theme } = useThemeStore()
  const isDark = theme === 'dark'

  const memoizedCircles = useMemo(() => {
    if (!showCircles) return null
    return towers.map((tower) => tower.radius_m ? (
      <Circle
        key={`circle-${tower.id}`}
        center={[tower.lat, tower.lng]}
        radius={tower.radius_m}
        pathOptions={{
          color: tower.confidenceTier === 'Known' ? '#10b981' : tower.confidenceTier === 'Estimated' ? '#f59e0b' : '#ef4444',
          fillColor: tower.confidenceTier === 'Known' ? '#10b981' : tower.confidenceTier === 'Estimated' ? '#f59e0b' : '#ef4444',
          fillOpacity: tower.id === selectedTowerId ? 0.25 : 0.05,
          weight: tower.id === selectedTowerId ? 2 : 1,
          dashArray: '4, 4'
        }}
      />
    ) : null)
  }, [towers, showCircles, selectedTowerId])

  const memoizedMarkers = useMemo(() => {
    if (!showMarkers) return null
    return towers.map((tower) => {
      const isSelected = tower.id === selectedTowerId
      return (
        <Marker
          key={tower.id}
          position={[tower.lat, tower.lng]}
          icon={ICONS[tower.confidenceTier](isSelected)}
          eventHandlers={{
            click: () => onSelectTower?.(tower.id)
          }}
        >
          <Popup>
            <div className="p-1">
              <p className="font-bold text-sm mb-1 text-slate-900">{tower.name || tower.id}</p>
              <p className="text-xs text-gray-600 mb-1">
                Tier: <span className="font-semibold text-slate-800">{tower.confidenceTier}</span>
              </p>
              <p className="text-xs font-mono text-gray-500">
                {tower.lat.toFixed(4)}, {tower.lng.toFixed(4)}
              </p>
              {tower.radius_m && (
                <p className="text-xs text-gray-500 mt-1">
                  Radius: {tower.radius_m}m
                </p>
              )}
            </div>
          </Popup>
        </Marker>
      )
    })
  }, [towers, showMarkers, selectedTowerId, onSelectTower])

  // Dynamic Tile URL based on active theme
  const tileUrl = isDark
    ? 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
    : 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png'

  // Filter path coordinates: ignore micro-jitter (<200m) AND ignore long teleports (>15km / 0.0225 deg)
  const cleanPath = (pathCoordinates && pathCoordinates.length > 1) 
    ? pathCoordinates.filter((pt, idx) => {
        if (idx === 0) return true
        const prev = pathCoordinates[idx - 1]
        const distSq = Math.pow(pt[0] - prev[0], 2) + Math.pow(pt[1] - prev[1], 2)
        return distSq > 0.00002 && distSq < 0.0225 // Between ~200m and ~15km
      })
    : []

  return (
    <div className="w-full h-full min-h-[450px] rounded-xl overflow-hidden border border-border-primary relative">
      <MapContainer 
        center={center} 
        zoom={zoom} 
        style={{ 
          height: '100%', 
          width: '100%', 
          minHeight: '450px', 
          background: isDark ? '#0b0f19' : '#f8fafc' 
        }}
      >
        <MapUpdater 
          center={center} 
          zoom={zoom} 
          towers={towers} 
          pathCoordinates={cleanPath} 
          heatmapPoints={heatmapPoints} 
        />
        
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url={tileUrl}
        />

        {/* Heatmap Layer (Mounts/Unmounts cleanly based on showHeatmap state) */}
        {showHeatmap && heatmapPoints && heatmapPoints.length > 0 && (
          <HeatmapLayer 
            points={heatmapPoints} 
            radius={32} 
            blur={22} 
            minOpacity={isDark ? 0.2 : 0.25}
          />
        )}

        {/* Smoothed Path (Kalman) */}
        {showPath && cleanPath.length > 1 && (
          <Polyline
            positions={cleanPath}
            pathOptions={{ 
              color: isDark ? '#818cf8' : '#4f46e5', 
              weight: 3, 
              opacity: 0.7,
              lineCap: 'round',
              lineJoin: 'round',
            }}
          />
        )}

        {/* Confidence Circles Layer */}
        {showCircles && (
          <LayerGroup>
            {memoizedCircles}
          </LayerGroup>
        )}

        {/* Tower Markers Layer - Clustered */}
        {showMarkers && (
          <MarkerClusterGroup 
            chunkedLoading
            maxClusterRadius={50}
          >
            {memoizedMarkers}
          </MarkerClusterGroup>
        )}
      </MapContainer>
    </div>
  )
}

export default LeafletMap
