"""
Tower Density & CGI Resolution Fallbacks Engine
===============================================

Implements lookup fallback systems to resolve Cell Global Identity (CGI) entries
and spatial density metrics for cell towers within the Asterion scientific pipeline.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from scientific.constants import haversine_distance_m


def parse_cgi(cgi_str: str) -> Dict[str, Optional[str]]:
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

    def __init__(self, towers: List[Any]) -> None:
        """Initialize the resolver with a list/registry of towers.

        Towers can be dictionaries, Pydantic objects, or ORM models.
        Must have coordinates (latitude, longitude) and CGI-associated fields (e.g. cgi, tower_id, or mcc/mnc/lac/ci).
        """
        self.towers = towers
        self._parsed_towers: List[Dict[str, Any]] = []
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

    def resolve_cgi(self, q_cgi: str) -> Dict[str, Any]:
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
            matches: List[dict],
        ) -> Tuple[Optional[float], Optional[float]]:
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
            mcc_matches = [
                t for t in self._parsed_towers if t["mcc"] == q_mcc
            ]
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
    towers: List[Any],
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
    towers: List[Any],
    radius_m: float = 1000.0,
) -> Dict[str, int]:
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
        count = calculate_radius_density(
            float(t_lat), float(t_lon), towers, radius_m
        )
        densities[str(t_id)] = count

    return densities


def calculate_grid_density(
    towers: List[Any],
    grid_size_deg: float = 0.01,
) -> Dict[Tuple[float, float], int]:
    """Group towers into spatial grid cells and compute the count per cell.

    Args:
        towers: List of tower objects/dicts.
        grid_size_deg: Grid cell dimensions in degrees (default 0.01).

    Returns:
        A dictionary mapping (grid_latitude_center, grid_longitude_center) to tower count.
    """
    grid = {}
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


def normalize_densities(densities: Dict[Any, float]) -> Dict[Any, float]:
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
