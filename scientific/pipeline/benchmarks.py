"""
Tower Density, CGI Resolution Fallbacks & Pipeline Validation Benchmarks
========================================================================

Implements lookup fallback systems to resolve Cell Global Identity (CGI) entries,
spatial density metrics for cell towers, and pipeline validation benchmark routines
within the Asterion scientific pipeline.

Benchmark capabilities:
    - Coordinate accuracy evaluation against known reference towers
    - Validation pass rate (validated records / total records)
    - Tower resolution rate (Known + Estimated / total towers)
    - Unknown tower percentage per operator
    - Kalman improvement factor (raw vs. smoothed path error comparison)
"""

import re
import statistics
from dataclasses import dataclass, field
from typing import Any

from scientific.constants import haversine_distance_m


def parse_cgi(cgi_str: str) -> dict[str, str | None]:
    """Parse a delimited Cell Global Identity (CGI) string into its components.

    Standard format: MCC-MNC-LAC-CI (e.g. '404-98-8331-23071').
    Supports separators like '-', ':', '/', or whitespace.

    Returns:
        A dictionary with keys: 'mcc', 'mnc', 'lac', 'ci'.
        Missing components are set to None.
    """
    if not cgi_str:
        return {"mcc": None, "mnc": None, "lac": None, "ci": None}

    # Split on any combination of hyphen, colon, slash, or whitespace
    parts = re.split(r"[-:\s/]+", cgi_str.strip())

    # Map the parts based on length
    mcc = parts[0] if len(parts) > 0 and parts[0] else None
    mnc = parts[1] if len(parts) > 1 and parts[1] else None
    lac = parts[2] if len(parts) > 2 and parts[2] else None
    ci = parts[3] if len(parts) > 3 and parts[3] else None

    return {"mcc": mcc, "mnc": mnc, "lac": lac, "ci": ci}


class CGIResolver:
    """Resolves coordinates and details for a queried CGI with prefix-based fallback rules.

    Fallback layers:
      1. Exact Match (MCC-MNC-LAC-CI)
      2. LAC Prefix Match (MCC-MNC-LAC) -> centroid of all matching towers
      3. MNC Prefix Match (MCC-MNC) -> centroid of all matching towers
      4. MCC Prefix Match (MCC) -> centroid of all matching towers
    """

    def __init__(self, towers: list[Any]) -> None:
        """Initialize the resolver with a list/registry of towers.

        Towers can be dictionaries, Pydantic objects, or ORM models.
        Must have coordinates (latitude, longitude) and CGI-associated fields (e.g. cgi, tower_id, or mcc/mnc/lac/ci).
        """
        self.towers = towers
        self._parsed_towers: list[dict[str, Any]] = []
        self._initialize_registry()

    def _get_val(self, obj: Any, key: str) -> Any:
        """Retrieve value from dict or object attribute."""
        if isinstance(obj, dict):
            return obj.get(key)
        return getattr(obj, key, None)

    def _initialize_registry(self) -> None:
        """Pre-parse and index towers for fast lookup."""
        for t in self.towers:
            # Try to get explicit components first
            mcc = self._get_val(t, "mcc")
            mnc = self._get_val(t, "mnc")
            lac = self._get_val(t, "lac")
            ci = self._get_val(t, "ci")

            lat = self._get_val(t, "latitude")
            lon = self._get_val(t, "longitude")

            # Try to extract CGI string
            cgi_str = self._get_val(t, "cgi")
            if cgi_str is None:
                cgi_str = self._get_val(t, "tower_id")
            if cgi_str is None:
                cgi_str = self._get_val(t, "tower_name")

            # If components are not explicit, parse the CGI string
            if mcc is None or mnc is None or lac is None or ci is None:
                if cgi_str:
                    parsed = parse_cgi(cgi_str)
                    mcc = mcc or parsed["mcc"]
                    mnc = mnc or parsed["mnc"]
                    lac = lac or parsed["lac"]
                    ci = ci or parsed["ci"]

            # Store the normalized tower structure
            self._parsed_towers.append(
                {
                    "mcc": str(mcc) if mcc is not None else None,
                    "mnc": str(mnc) if mnc is not None else None,
                    "lac": str(lac) if lac is not None else None,
                    "ci": str(ci) if ci is not None else None,
                    "latitude": float(lat) if lat is not None else None,
                    "longitude": float(lon) if lon is not None else None,
                    "original": t,
                    "cgi": cgi_str,
                }
            )

    def resolve_cgi(self, q_cgi: str) -> dict[str, Any]:
        """Resolve a query Cell Global Identity (CGI) string to coordinates and metadata.

        Returns:
            A dictionary containing:
              - resolved_latitude: float or None
              - resolved_longitude: float or None
              - resolution_method: str ('exact', 'prefix_lac', 'prefix_mnc', 'prefix_mcc', 'unresolved')
              - matched_towers_count: int
        """
        parsed_query = parse_cgi(q_cgi)
        q_mcc = str(parsed_query["mcc"]) if parsed_query["mcc"] is not None else None
        q_mnc = str(parsed_query["mnc"]) if parsed_query["mnc"] is not None else None
        q_lac = str(parsed_query["lac"]) if parsed_query["lac"] is not None else None
        q_ci = str(parsed_query["ci"]) if parsed_query["ci"] is not None else None

        # Helper to compute centroid/mean of list of parsed towers
        def compute_mean_coords(
            matches: list[dict],
        ) -> tuple[float | None, float | None]:
            valid_coords = [
                (t["latitude"], t["longitude"])
                for t in matches
                if t["latitude"] is not None and t["longitude"] is not None
            ]
            if not valid_coords:
                return None, None
            mean_lat = sum(c[0] for c in valid_coords) / len(valid_coords)
            mean_lon = sum(c[1] for c in valid_coords) / len(valid_coords)
            return mean_lat, mean_lon

        # 1. Try Exact Match (MCC, MNC, LAC, CI)
        if q_mcc and q_mnc and q_lac and q_ci:
            exact_matches = [
                t
                for t in self._parsed_towers
                if t["mcc"] == q_mcc
                and t["mnc"] == q_mnc
                and t["lac"] == q_lac
                and t["ci"] == q_ci
            ]
            lat, lon = compute_mean_coords(exact_matches)
            if lat is not None and lon is not None:
                return {
                    "resolved_latitude": lat,
                    "resolved_longitude": lon,
                    "resolution_method": "exact",
                    "matched_towers_count": len(exact_matches),
                }

        # 2. Try LAC Prefix Fallback (MCC, MNC, LAC)
        if q_mcc and q_mnc and q_lac:
            lac_matches = [
                t
                for t in self._parsed_towers
                if t["mcc"] == q_mcc and t["mnc"] == q_mnc and t["lac"] == q_lac
            ]
            lat, lon = compute_mean_coords(lac_matches)
            if lat is not None and lon is not None:
                return {
                    "resolved_latitude": lat,
                    "resolved_longitude": lon,
                    "resolution_method": "prefix_lac",
                    "matched_towers_count": len(lac_matches),
                }

        # 3. Try MNC Prefix Fallback (MCC, MNC)
        if q_mcc and q_mnc:
            mnc_matches = [
                t
                for t in self._parsed_towers
                if t["mcc"] == q_mcc and t["mnc"] == q_mnc
            ]
            lat, lon = compute_mean_coords(mnc_matches)
            if lat is not None and lon is not None:
                return {
                    "resolved_latitude": lat,
                    "resolved_longitude": lon,
                    "resolution_method": "prefix_mnc",
                    "matched_towers_count": len(mnc_matches),
                }

        # 4. Try MCC Prefix Fallback (MCC)
        if q_mcc:
            mcc_matches = [t for t in self._parsed_towers if t["mcc"] == q_mcc]
            lat, lon = compute_mean_coords(mcc_matches)
            if lat is not None and lon is not None:
                return {
                    "resolved_latitude": lat,
                    "resolved_longitude": lon,
                    "resolution_method": "prefix_mcc",
                    "matched_towers_count": len(mcc_matches),
                }

        # 5. Unresolved
        return {
            "resolved_latitude": None,
            "resolved_longitude": None,
            "resolution_method": "unresolved",
            "matched_towers_count": 0,
        }


def calculate_radius_density(
    lat: float,
    lon: float,
    towers: list[Any],
    radius_m: float = 1000.0,
) -> int:
    """Calculate the number of towers located within radius_m of the given coordinates.

    Args:
        lat: Target latitude.
        lon: Target longitude.
        towers: List of tower objects/dicts with 'latitude' and 'longitude'.
        radius_m: The search radius in meters (default 1000.0).

    Returns:
        The count of towers within the radius.
    """
    count = 0
    for t in towers:
        t_lat = (
            getattr(t, "latitude", None)
            if not isinstance(t, dict)
            else t.get("latitude")
        )
        t_lon = (
            getattr(t, "longitude", None)
            if not isinstance(t, dict)
            else t.get("longitude")
        )

        if t_lat is not None and t_lon is not None:
            dist = haversine_distance_m(lat, lon, float(t_lat), float(t_lon))
            if dist <= radius_m:
                count += 1
    return count


def calculate_neighbor_density(
    towers: list[Any],
    radius_m: float = 1000.0,
) -> dict[str, int]:
    """Calculate the density of neighboring towers around each tower.

    Args:
        towers: List of tower objects/dicts. Each must have a unique identifier (tower_id or cgi)
                and coordinates (latitude, longitude).
        radius_m: Distance threshold in meters (default 1000.0).

    Returns:
        A dictionary mapping each tower's identifier to its neighbor count.
        Note: The count includes the tower itself if it falls within the radius (which is always true
        if coordinates are valid, so the minimum neighbor count is 1 for a tower with valid coordinates).
    """
    densities = {}
    for t in towers:
        t_id = getattr(t, "tower_id", None) or getattr(t, "cgi", None)
        if isinstance(t, dict):
            t_id = t.get("tower_id") or t.get("cgi") or t.get("tower_name")

        if not t_id:
            continue

        t_lat = (
            getattr(t, "latitude", None)
            if not isinstance(t, dict)
            else t.get("latitude")
        )
        t_lon = (
            getattr(t, "longitude", None)
            if not isinstance(t, dict)
            else t.get("longitude")
        )

        if t_lat is None or t_lon is None:
            densities[str(t_id)] = 0
            continue

        # Count other towers
        count = calculate_radius_density(float(t_lat), float(t_lon), towers, radius_m)
        densities[str(t_id)] = count

    return densities


def calculate_grid_density(
    towers: list[Any],
    grid_size_deg: float = 0.01,
) -> dict[tuple[float, float], int]:
    """Group towers into spatial grid cells and compute the count per cell.

    Args:
        towers: List of tower objects/dicts.
        grid_size_deg: Grid cell dimensions in degrees (default 0.01).

    Returns:
        A dictionary mapping (grid_latitude_center, grid_longitude_center) to tower count.
    """
    grid: dict[tuple[float, float], int] = {}
    for t in towers:
        t_lat = (
            getattr(t, "latitude", None)
            if not isinstance(t, dict)
            else t.get("latitude")
        )
        t_lon = (
            getattr(t, "longitude", None)
            if not isinstance(t, dict)
            else t.get("longitude")
        )

        if t_lat is not None and t_lon is not None:
            # Round coordinates to nearest grid cell center
            grid_lat = round(float(t_lat) / grid_size_deg) * grid_size_deg
            grid_lon = round(float(t_lon) / grid_size_deg) * grid_size_deg
            cell = (round(grid_lat, 6), round(grid_lon, 6))
            grid[cell] = grid.get(cell, 0) + 1
    return grid


def normalize_densities(densities: dict[Any, float]) -> dict[Any, float]:
    """Normalize density scores to the interval [0.0, 1.0] using Min-Max scaling.

    If the maximum and minimum densities are equal, returns 1.0 for all entries.
    """
    if not densities:
        return {}

    min_val = min(densities.values())
    max_val = max(densities.values())
    range_val = max_val - min_val

    normalized = {}
    for k, v in densities.items():
        if range_val == 0.0:
            normalized[k] = 1.0
        else:
            normalized[k] = (v - min_val) / range_val
    return normalized


# ═══════════════════════════════════════════════════════════════════════════
# Pipeline Validation Benchmarks
# ═══════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class CoordinateAccuracyResult:
    """Per-tower coordinate accuracy evaluation against a known reference.

    Attributes:
        tower_id: Identifier of the evaluated tower.
        reference_latitude: Known ground-truth latitude (WGS84).
        reference_longitude: Known ground-truth longitude (WGS84).
        computed_latitude: Pipeline-computed latitude (WGS84).
        computed_longitude: Pipeline-computed longitude (WGS84).
        error_distance_m: Haversine distance between reference and computed (meters).
        is_within_threshold: True if error_distance_m ≤ threshold.
    """

    tower_id: str
    reference_latitude: float
    reference_longitude: float
    computed_latitude: float
    computed_longitude: float
    error_distance_m: float
    is_within_threshold: bool


@dataclass(frozen=True)
class BenchmarkMetrics:
    """Aggregated pipeline validation benchmark results.

    All metrics are deterministic and reproducible given identical inputs.

    Attributes:
        validation_pass_rate: Fraction of validated records (0.0–1.0).
        tower_resolution_rate: Fraction of Known + Estimated towers (0.0–1.0).
        unknown_tower_pct_by_operator: Per-operator unknown tower percentage.
        kalman_improvement_factor: Ratio of mean raw error to mean smoothed error (≥ 1.0).
        coordinate_accuracy_results: Per-tower accuracy evaluations.
        mean_error_m: Mean coordinate error across evaluated towers (meters).
        median_error_m: Median coordinate error across evaluated towers (meters).
        max_error_m: Maximum coordinate error across evaluated towers (meters).
        accuracy_within_threshold_pct: Percentage of towers within accuracy threshold.
        accuracy_threshold_m: The threshold used for within-threshold calculation (meters).
    """

    validation_pass_rate: float
    tower_resolution_rate: float
    unknown_tower_pct_by_operator: dict[str, float] = field(default_factory=dict)
    kalman_improvement_factor: float = 1.0
    coordinate_accuracy_results: list[CoordinateAccuracyResult] = field(
        default_factory=list,
    )
    mean_error_m: float = 0.0
    median_error_m: float = 0.0
    max_error_m: float = 0.0
    accuracy_within_threshold_pct: float = 0.0
    accuracy_threshold_m: float = 500.0


def evaluate_coordinate_accuracy(
    reference_towers: list[dict[str, Any]],
    computed_towers: list[dict[str, Any]],
    threshold_m: float = 500.0,
) -> list[CoordinateAccuracyResult]:
    """Evaluate computed tower coordinates against known reference coordinates.

    Each reference tower is matched to a computed tower by ``tower_id``.
    The Haversine distance between reference and computed coordinates is
    calculated as the error distance.

    Args:
        reference_towers: List of dicts with keys:
            ``tower_id``, ``latitude``, ``longitude``.
        computed_towers: List of dicts with keys:
            ``tower_id``, ``latitude``, ``longitude``.
        threshold_m: Accuracy threshold in meters (default 500.0).

    Returns:
        A list of :class:`CoordinateAccuracyResult` for each matched pair.
    """
    computed_map: dict[str, dict[str, Any]] = {
        str(t.get("tower_id", "")): t for t in computed_towers
    }

    results: list[CoordinateAccuracyResult] = []

    for ref in reference_towers:
        tid = str(ref.get("tower_id", ""))
        if tid not in computed_map:
            continue

        comp = computed_map[tid]

        ref_lat = float(ref["latitude"])
        ref_lon = float(ref["longitude"])
        comp_lat = float(comp["latitude"])
        comp_lon = float(comp["longitude"])

        error_m = haversine_distance_m(ref_lat, ref_lon, comp_lat, comp_lon)

        results.append(
            CoordinateAccuracyResult(
                tower_id=tid,
                reference_latitude=ref_lat,
                reference_longitude=ref_lon,
                computed_latitude=comp_lat,
                computed_longitude=comp_lon,
                error_distance_m=round(error_m, 4),
                is_within_threshold=error_m <= threshold_m,
            )
        )

    return results


def calculate_validation_pass_rate(
    validated_records: int,
    total_records: int,
) -> float:
    """Calculate the validation pass rate as a fraction.

    Args:
        validated_records: Number of records that passed validation.
        total_records: Total number of records processed.

    Returns:
        Validation pass rate in ``[0.0, 1.0]``. Returns ``0.0`` if
        total_records is zero.
    """
    if total_records <= 0:
        return 0.0
    return round(validated_records / total_records, 6)


def calculate_tower_resolution_rate(
    tower_data: list[dict[str, Any]],
) -> float:
    """Calculate the tower resolution rate (Known + Estimated / total).

    Resolution methods are classified as:
        - **Known**: ``exact``
        - **Estimated**: ``prefix_lac``, ``prefix_mnc``, ``prefix_mcc``
        - **Unknown**: ``unresolved`` or missing

    Args:
        tower_data: List of tower dicts with ``resolution_method`` key.

    Returns:
        Tower resolution rate in ``[0.0, 1.0]``. Returns ``0.0`` if
        the tower list is empty.
    """
    if not tower_data:
        return 0.0

    resolved_count = 0
    for tower in tower_data:
        method = str(tower.get("resolution_method", "unresolved")).lower()
        if method in ("exact", "prefix_lac", "prefix_mnc", "prefix_mcc"):
            resolved_count += 1

    return round(resolved_count / len(tower_data), 6)


def calculate_unknown_tower_pct_by_operator(
    tower_data: list[dict[str, Any]],
) -> dict[str, float]:
    """Calculate the unknown tower percentage for each operator.

    Args:
        tower_data: List of tower dicts with ``operator`` and
            ``resolution_method`` keys.

    Returns:
        A dictionary mapping operator name to the percentage of
        unresolved towers (0.0–100.0).
    """
    if not tower_data:
        return {}

    # Group towers by operator
    operator_totals: dict[str, int] = {}
    operator_unknown: dict[str, int] = {}

    for tower in tower_data:
        operator = str(tower.get("operator", "Unknown"))
        method = str(tower.get("resolution_method", "unresolved")).lower()

        operator_totals[operator] = operator_totals.get(operator, 0) + 1

        if method not in ("exact", "prefix_lac", "prefix_mnc", "prefix_mcc"):
            operator_unknown[operator] = operator_unknown.get(operator, 0) + 1

    result: dict[str, float] = {}
    for operator, total in operator_totals.items():
        unknown = operator_unknown.get(operator, 0)
        result[operator] = round((unknown / total) * 100.0, 2)

    return result


def calculate_kalman_improvement_factor(
    raw_errors: list[float],
    smoothed_errors: list[float],
) -> float:
    """Calculate the Kalman improvement factor from raw vs. smoothed errors.

    The improvement factor is defined as::

        factor = mean(raw_errors) / mean(smoothed_errors)

    A factor > 1.0 indicates the Kalman filter improved accuracy.
    The factor is floored at 1.0 — if smoothing worsened accuracy,
    the factor is clamped to 1.0 to indicate no improvement.

    Args:
        raw_errors: List of raw path error distances (meters).
        smoothed_errors: List of smoothed path error distances (meters).

    Returns:
        Kalman improvement factor (≥ 1.0). Returns ``1.0`` if either
        list is empty or the smoothed mean is zero.
    """
    if not raw_errors or not smoothed_errors:
        return 1.0

    mean_raw = statistics.mean(raw_errors)
    mean_smoothed = statistics.mean(smoothed_errors)

    if mean_smoothed <= 0.0:
        return 1.0

    factor = mean_raw / mean_smoothed
    return round(max(1.0, factor), 6)


def run_pipeline_benchmarks(
    *,
    validated_records: int = 0,
    total_records: int = 0,
    tower_data: list[dict[str, Any]] | None = None,
    reference_towers: list[dict[str, Any]] | None = None,
    computed_towers: list[dict[str, Any]] | None = None,
    raw_errors: list[float] | None = None,
    smoothed_errors: list[float] | None = None,
    accuracy_threshold_m: float = 500.0,
) -> BenchmarkMetrics:
    """Orchestrate all pipeline benchmark calculations.

    This is the primary entry point for running the complete benchmark
    suite.  All calculations are deterministic and reproducible.

    Args:
        validated_records: Number of records that passed validation.
        total_records: Total number of records processed.
        tower_data: Tower resolution data with ``resolution_method`` and
            ``operator`` keys.
        reference_towers: Known reference tower coordinates.
        computed_towers: Pipeline-computed tower coordinates.
        raw_errors: Raw path error distances (meters) for Kalman comparison.
        smoothed_errors: Smoothed path error distances (meters) for Kalman comparison.
        accuracy_threshold_m: Coordinate accuracy threshold in meters.

    Returns:
        A :class:`BenchmarkMetrics` instance with all computed metrics.
    """
    _tower_data = tower_data or []
    _reference = reference_towers or []
    _computed = computed_towers or []
    _raw_errors = raw_errors or []
    _smoothed_errors = smoothed_errors or []

    # 1. Validation pass rate
    pass_rate = calculate_validation_pass_rate(validated_records, total_records)

    # 2. Tower resolution rate
    resolution_rate = calculate_tower_resolution_rate(_tower_data)

    # 3. Unknown tower percentage by operator
    unknown_pct = calculate_unknown_tower_pct_by_operator(_tower_data)

    # 4. Kalman improvement factor
    kalman_factor = calculate_kalman_improvement_factor(_raw_errors, _smoothed_errors)

    # 5. Coordinate accuracy evaluation
    accuracy_results = evaluate_coordinate_accuracy(
        _reference,
        _computed,
        accuracy_threshold_m,
    )

    # 6. Aggregate accuracy statistics
    error_distances = [r.error_distance_m for r in accuracy_results]

    if error_distances:
        mean_err = round(statistics.mean(error_distances), 4)
        median_err = round(statistics.median(error_distances), 4)
        max_err = round(max(error_distances), 4)
        within_count = sum(1 for r in accuracy_results if r.is_within_threshold)
        within_pct = round((within_count / len(accuracy_results)) * 100.0, 2)
    else:
        mean_err = 0.0
        median_err = 0.0
        max_err = 0.0
        within_pct = 0.0

    return BenchmarkMetrics(
        validation_pass_rate=pass_rate,
        tower_resolution_rate=resolution_rate,
        unknown_tower_pct_by_operator=unknown_pct,
        kalman_improvement_factor=kalman_factor,
        coordinate_accuracy_results=accuracy_results,
        mean_error_m=mean_err,
        median_error_m=median_err,
        max_error_m=max_err,
        accuracy_within_threshold_pct=within_pct,
        accuracy_threshold_m=accuracy_threshold_m,
    )
