import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type MapTileProvider = 'osm' | 'carto-dark' | 'carto-light'

interface AppSettingsState {
  /** Base URL for backend API calls */
  apiBaseUrl: string
  /** Leaflet map tile provider */
  mapTileProvider: MapTileProvider
  /** Default map center coordinates [lat, lng] */
  defaultMapCenter: [number, number]
  /** Default map zoom level */
  defaultMapZoom: number

  setApiBaseUrl: (url: string) => void
  setMapTileProvider: (provider: MapTileProvider) => void
  setDefaultMapCenter: (center: [number, number]) => void
  setDefaultMapZoom: (zoom: number) => void
}

/**
 * Application settings store with localStorage persistence.
 * Holds global configuration for API connectivity, map defaults,
 * and other workspace preferences.
 */
export const useAppSettingsStore = create<AppSettingsState>()(
  persist(
    (set) => ({
      apiBaseUrl: import.meta.env.VITE_API_URL ?? 'http://localhost:8001',
      mapTileProvider: 'carto-dark',
      defaultMapCenter: [20.5937, 78.9629], // Center of India
      defaultMapZoom: 5,

      setApiBaseUrl: (url: string) => set({ apiBaseUrl: url }),
      setMapTileProvider: (provider: MapTileProvider) =>
        set({ mapTileProvider: provider }),
      setDefaultMapCenter: (center: [number, number]) =>
        set({ defaultMapCenter: center }),
      setDefaultMapZoom: (zoom: number) => set({ defaultMapZoom: zoom }),
    }),
    {
      name: 'asterion-app-settings',
    },
  ),
)
