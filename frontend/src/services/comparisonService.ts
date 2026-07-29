import { api } from '@/lib/api';
import { simulationService } from './simulationService';
import { evidenceService } from './evidenceService';

// ── Types ────────────────────────────────────────────────────────────────

export interface CaseComparisonMetrics {
  caseId: number;
  caseCode: string;
  measurementCount: number;
  towerCount: number;
  avgRssi: number | null;
  minRssi: number | null;
  maxRssi: number | null;
  validRate: number;
  hasCoords: boolean;
  hasEvidence: boolean;
  reproducibilityHash: string | null;
  avgUncertainty: number | null;
  towerIds: string[];
}

export interface ComparisonResult {
  metricsA: CaseComparisonMetrics;
  metricsB: CaseComparisonMetrics;
  overlappingTowerIds: string[];
  overlappingTowerCount: number;
  uniqueTowersA: number;
  uniqueTowersB: number;
  measurementCountDiff: number;
  avgRssiDiff: number | null;
  overlapPercentage: number;
}

// ── Service ──────────────────────────────────────────────────────────────

export const comparisonService = {
  /**
   * Attempt to call the backend comparison endpoint.
   * Falls back to client-side computation if the endpoint is unavailable.
   *
   * GET /cases/compare?case_a={id}&case_b={id}
   */
  compareCase: async (
    caseAId: number,
    caseBId: number,
  ): Promise<ComparisonResult> => {
    // Try the backend compare endpoint first
    try {
      const { data } = await api.get<ComparisonResult>(
        `/cases/compare?case_a=${caseAId}&case_b=${caseBId}`,
      );
      return data;
    } catch {
      // Backend endpoint not available — compute client-side
    }

    // ── Client-side fallback ──────────────────────────────────────────
    const caseCodeA = `CASE-${String(caseAId).padStart(3, '0')}`;
    const caseCodeB = `CASE-${String(caseBId).padStart(3, '0')}`;

    const [metricsA, metricsB] = await Promise.all([
      comparisonService._buildMetrics(caseAId, caseCodeA),
      comparisonService._buildMetrics(caseBId, caseCodeB),
    ]);

    // Compute overlap
    const setA = new Set(metricsA.towerIds);
    const setB = new Set(metricsB.towerIds);
    const overlappingTowerIds = metricsA.towerIds.filter((id) => setB.has(id));
    const allTowerIds = new Set([...metricsA.towerIds, ...metricsB.towerIds]);

    return {
      metricsA,
      metricsB,
      overlappingTowerIds,
      overlappingTowerCount: overlappingTowerIds.length,
      uniqueTowersA: setA.size - overlappingTowerIds.length,
      uniqueTowersB: setB.size - overlappingTowerIds.length,
      measurementCountDiff: Math.abs(
        metricsA.measurementCount - metricsB.measurementCount,
      ),
      avgRssiDiff:
        metricsA.avgRssi != null && metricsB.avgRssi != null
          ? Math.abs(metricsA.avgRssi - metricsB.avgRssi)
          : null,
      overlapPercentage:
        allTowerIds.size > 0
          ? Math.round((overlappingTowerIds.length / allTowerIds.size) * 100)
          : 0,
    };
  },

  /**
   * Build metrics for a single case by fetching measurements & evidence.
   */
  _buildMetrics: async (
    caseId: number,
    caseCode: string,
  ): Promise<CaseComparisonMetrics> => {
    let measurements: any[] = [];
    let evidence: any = null;

    try {
      measurements = await simulationService.getMeasurements(caseCode);
    } catch {
      /* no measurements */
    }

    try {
      evidence = await evidenceService.getEvidence(caseCode);
    } catch {
      /* no evidence */
    }

    const rssiValues = measurements
      .map((m: any) => m.rssi_dbm)
      .filter((v: any) => typeof v === 'number');

    const towerIds = [
      ...new Set(
        measurements
          .map((m: any) => m.tower_id || m.measurement_code?.split('-')?.[2])
          .filter(Boolean) as string[],
      ),
    ];

    const validCount = measurements.filter(
      (m: any) => m.rssi_dbm >= -110,
    ).length;
    const totalCount = measurements.length;

    const uncertainties = measurements
      .map((m: any) => m.uncertainty_m)
      .filter((v: any) => typeof v === 'number');

    return {
      caseId,
      caseCode,
      measurementCount: totalCount,
      towerCount: towerIds.length,
      avgRssi:
        rssiValues.length > 0
          ? rssiValues.reduce((a: number, b: number) => a + b, 0) /
            rssiValues.length
          : null,
      minRssi: rssiValues.length > 0 ? Math.min(...rssiValues) : null,
      maxRssi: rssiValues.length > 0 ? Math.max(...rssiValues) : null,
      validRate: totalCount > 0 ? Math.round((validCount / totalCount) * 100) : 0,
      hasCoords: measurements.some(
        (m: any) => m.latitude != null && m.longitude != null,
      ),
      hasEvidence: !!evidence,
      reproducibilityHash: evidence?.reproducibility_hash || null,
      avgUncertainty:
        uncertainties.length > 0
          ? Math.round(
              uncertainties.reduce((a: number, b: number) => a + b, 0) /
                uncertainties.length,
            )
          : null,
      towerIds,
    };
  },
};
