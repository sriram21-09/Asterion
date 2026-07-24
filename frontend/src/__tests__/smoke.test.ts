import { describe, it, expect } from 'vitest';
import { useNavigationStore } from '@/stores/useNavigationStore';
import { useAppSettingsStore } from '@/stores/useAppSettingsStore';

describe('Frontend Infrastructure & Store Smoke Tests', () => {
  it('useNavigationStore initializes with sidebar closed', () => {
    const state = useNavigationStore.getState();
    expect(state.sidebarOpen).toBe(false);
    expect(typeof state.toggleSidebar).toBe('function');
    expect(typeof state.setSidebarOpen).toBe('function');
  });

  it('useNavigationStore toggleSidebar works', () => {
    const { toggleSidebar } = useNavigationStore.getState();
    toggleSidebar();
    expect(useNavigationStore.getState().sidebarOpen).toBe(true);
    toggleSidebar();
    expect(useNavigationStore.getState().sidebarOpen).toBe(false);
  });

  it('useAppSettingsStore initializes with default map settings', () => {
    const state = useAppSettingsStore.getState();
    expect(state.apiBaseUrl).toBeDefined();
    expect(state.mapTileProvider).toBe('carto-dark');
    expect(state.defaultMapCenter).toEqual([20.5937, 78.9629]);
    expect(state.defaultMapZoom).toBe(5);
  });

  it('useAppSettingsStore setters are defined', () => {
    const state = useAppSettingsStore.getState();
    expect(typeof state.setApiBaseUrl).toBe('function');
    expect(typeof state.setMapTileProvider).toBe('function');
    expect(typeof state.setDefaultMapCenter).toBe('function');
    expect(typeof state.setDefaultMapZoom).toBe('function');
  });
});
