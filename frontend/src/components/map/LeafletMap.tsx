import { useEffect } from 'react'
import { MapContainer, TileLayer, Marker, Popup, useMap, Polyline, LayersControl, LayerGroup, Circle } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

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
  center?: [number, number]
  zoom?: number
  pathCoordinates?: [number, number][]
}

// Custom icons based on confidence tier
const createCustomIcon = (color: string) => {
  return L.divIcon({
    className: 'custom-leaflet-marker',
    html: `
      <div style="
        background-color: ${color};
        width: 16px;
        height: 16px;
        border-radius: 50%;
        border: 2px solid white;
        box-shadow: 0 0 4px rgba(0,0,0,0.5);
      "></div>
    `,
    iconSize: [16, 16],
    iconAnchor: [8, 8],
    popupAnchor: [0, -8],
  })
}

const ICONS = {
  Known: createCustomIcon('#10b981'),     // Emerald 500
  Estimated: createCustomIcon('#f59e0b'), // Amber 500
  Unknown: createCustomIcon('#ef4444'),   // Red 500
}

function MapUpdater({ center, zoom }: { center: [number, number], zoom: number }) {
  const map = useMap()
  useEffect(() => {
    map.setView(center, zoom)
  }, [center, zoom, map])
  return null
}

export function LeafletMap({ towers, center = [12.9716, 77.5946], zoom = 13, pathCoordinates }: LeafletMapProps) {
  return (
    <div className="w-full h-full min-h-[400px] rounded-xl overflow-hidden border border-border-primary">
      <MapContainer center={center} zoom={zoom} style={{ height: '100%', width: '100%', minHeight: '400px' }}>
        <MapUpdater center={center} zoom={zoom} />
        
        <LayersControl position="topright">
          <LayersControl.BaseLayer checked name="OpenStreetMap">
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
            />
          </LayersControl.BaseLayer>

          {/* Smoothed Path (Kalman) */}
          <LayersControl.Overlay checked name="Smoothed Path (Kalman)">
            <LayerGroup>
              {pathCoordinates && pathCoordinates.length > 1 && (
                <Polyline
                  positions={pathCoordinates}
                  pathOptions={{ 
                    color: '#3b82f6', 
                    weight: 4, 
                    opacity: 0.8,
                    dashArray: '8, 8',
                    lineCap: 'round',
                    lineJoin: 'round',
                    className: 'leaflet-animated-path'
                  }}
                />
              )}
            </LayerGroup>
          </LayersControl.Overlay>

          {/* Confidence Circles Layer */}
          <LayersControl.Overlay checked name="Confidence Area">
            <LayerGroup>
              {towers.map((tower) => tower.radius_m ? (
                <Circle
                  key={`circle-${tower.id}`}
                  center={[tower.lat, tower.lng]}
                  radius={tower.radius_m}
                  pathOptions={{
                    color: tower.confidenceTier === 'Known' ? '#10b981' : tower.confidenceTier === 'Estimated' ? '#f59e0b' : '#ef4444',
                    fillColor: tower.confidenceTier === 'Known' ? '#10b981' : tower.confidenceTier === 'Estimated' ? '#f59e0b' : '#ef4444',
                    fillOpacity: 0.1,
                    weight: 1,
                    dashArray: '4, 4'
                  }}
                />
              ) : null)}
            </LayerGroup>
          </LayersControl.Overlay>

          {/* Tower Markers Layer */}
          <LayersControl.Overlay checked name="Tower Markers">
            <LayerGroup>
              {towers.map((tower) => (
                <Marker
                  key={tower.id}
                  position={[tower.lat, tower.lng]}
                  icon={ICONS[tower.confidenceTier]}
                >
                  <Popup>
                    <div className="p-1">
                      <p className="font-bold text-sm mb-1">{tower.name || tower.id}</p>
                      <p className="text-xs text-gray-600 mb-1">
                        Tier: <span className="font-semibold">{tower.confidenceTier}</span>
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
              ))}
            </LayerGroup>
          </LayersControl.Overlay>
        </LayersControl>
      </MapContainer>
    </div>
  )
}

export default LeafletMap
