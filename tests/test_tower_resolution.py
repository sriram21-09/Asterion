"""
Unit Tests for Tower Resolution and Density Calculations
=========================================================

Verifies CGI parsing, prefix-based lookup fallback systems, and spatial density metrics.
"""

import pytest

from scientific.models.tower import Tower
from scientific.pipeline.benchmarks import (
    CGIResolver,
    calculate_grid_density,
    calculate_neighbor_density,
    calculate_radius_density,
    normalize_densities,
    parse_cgi,
)


def test_parse_cgi_standard():
    res = parse_cgi("404-98-8331-23071")
    assert res == {"mcc": "404", "mnc": "98", "lac": "8331", "ci": "23071"}


def test_parse_cgi_delimiters():
    res1 = parse_cgi("404:98/8331 23071")
    assert res1 == {"mcc": "404", "mnc": "98", "lac": "8331", "ci": "23071"}

    res2 = parse_cgi(" 404 - 98 : 8331 / 23071 ")
    assert res2 == {"mcc": "404", "mnc": "98", "lac": "8331", "ci": "23071"}


def test_parse_cgi_incomplete():
    res = parse_cgi("404-98")
    assert res == {"mcc": "404", "mnc": "98", "lac": None, "ci": None}

    res2 = parse_cgi("404")
    assert res2 == {"mcc": "404", "mnc": None, "lac": None, "ci": None}


def test_parse_cgi_empty():
    assert parse_cgi("") == {"mcc": None, "mnc": None, "lac": None, "ci": None}
    assert parse_cgi(None) == {"mcc": None, "mnc": None, "lac": None, "ci": None}


class TestCGIResolver:
    @pytest.fixture
    def registry_towers(self):
        # We define a registry with various towers for testing fallbacks
        return [
            # 1. Exact match tower
            {
                "mcc": "404",
                "mnc": "45",
                "lac": "1000",
                "ci": "1",
                "latitude": 10.0,
                "longitude": 20.0,
                "tower_id": "T_EXACT_1",
            },
            # 2. Towers in same LAC (mcc=404, mnc=45, lac=2000) for LAC fallback
            {
                "mcc": "404",
                "mnc": "45",
                "lac": "2000",
                "ci": "10",
                "latitude": 12.0,
                "longitude": 30.0,
                "tower_id": "T_LAC_1",
            },
            {
                "mcc": "404",
                "mnc": "45",
                "lac": "2000",
                "ci": "11",
                "latitude": 13.0,
                "longitude": 31.0,
                "tower_id": "T_LAC_2",
            },
            # 3. Tower in same LAC but coordinates are None (should be ignored in average)
            {
                "mcc": "404",
                "mnc": "45",
                "lac": "2000",
                "ci": "12",
                "latitude": None,
                "longitude": None,
                "tower_id": "T_LAC_NULL",
            },
            # 4. Towers in same MNC (mcc=404, mnc=50) for MNC fallback
            {
                "mcc": "404",
                "mnc": "50",
                "lac": "3000",
                "ci": "100",
                "latitude": 15.0,
                "longitude": 40.0,
                "tower_id": "T_MNC_1",
            },
            # 5. Towers in same MCC (mcc=405) for MCC fallback
            {
                "mcc": "405",
                "mnc": "10",
                "lac": "4000",
                "ci": "999",
                "latitude": 25.0,
                "longitude": 50.0,
                "tower_id": "T_MCC_1",
            },
            # 6. Tower represented as Pydantic model with CGI tower_id
            Tower(
                tower_id="404-45-5000-9",
                latitude=14.5,
                longitude=25.5,
                antenna_height_m=30,
            ),
        ]

    def test_resolve_exact_match(self, registry_towers):
        resolver = CGIResolver(registry_towers)
        res = resolver.resolve_cgi("404-45-1000-1")
        assert res["resolved_latitude"] == 10.0
        assert res["resolved_longitude"] == 20.0
        assert res["resolution_method"] == "exact"
        assert res["matched_towers_count"] == 1

    def test_resolve_exact_match_pydantic(self, registry_towers):
        resolver = CGIResolver(registry_towers)
        res = resolver.resolve_cgi("404-45-5000-9")
        assert res["resolved_latitude"] == 14.5
        assert res["resolved_longitude"] == 25.5
        assert res["resolution_method"] == "exact"
        assert res["matched_towers_count"] == 1

    def test_resolve_lac_fallback(self, registry_towers):
        resolver = CGIResolver(registry_towers)
        # CI 99 doesn't exist, should fall back to LAC 2000
        # Expected average coordinates of T_LAC_1 and T_LAC_2:
        # lat: (12.0 + 13.0) / 2 = 12.5
        # lon: (30.0 + 31.0) / 2 = 30.5
        res = resolver.resolve_cgi("404-45-2000-99")
        assert res["resolved_latitude"] == 12.5
        assert res["resolved_longitude"] == 30.5
        assert res["resolution_method"] == "prefix_lac"
        # 3 match the prefix (T_LAC_1, T_LAC_2, T_LAC_NULL)
        assert res["matched_towers_count"] == 3

    def test_resolve_mnc_fallback(self, registry_towers):
        resolver = CGIResolver(registry_towers)
        # LAC 9999 and CI 9999 don't exist, should fall back to MNC 50
        res = resolver.resolve_cgi("404-50-9999-9999")
        assert res["resolved_latitude"] == 15.0
        assert res["resolved_longitude"] == 40.0
        assert res["resolution_method"] == "prefix_mnc"
        assert res["matched_towers_count"] == 1

    def test_resolve_mcc_fallback(self, registry_towers):
        resolver = CGIResolver(registry_towers)
        # MNC 99, LAC 9999, CI 9999 don't exist, should fall back to MCC 405
        res = resolver.resolve_cgi("405-99-9999-9999")
        assert res["resolved_latitude"] == 25.0
        assert res["resolved_longitude"] == 50.0
        assert res["resolution_method"] == "prefix_mcc"
        assert res["matched_towers_count"] == 1

    def test_resolve_unresolved(self, registry_towers):
        resolver = CGIResolver(registry_towers)
        res = resolver.resolve_cgi("999-99-9999-9999")
        assert res["resolved_latitude"] is None
        assert res["resolved_longitude"] is None
        assert res["resolution_method"] == "unresolved"
        assert res["matched_towers_count"] == 0


class TestDensityCalculations:
    @pytest.fixture
    def towers(self):
        return [
            {"tower_id": "T1", "latitude": 12.9716, "longitude": 77.5946},
            {"tower_id": "T2", "latitude": 12.9750, "longitude": 77.5900},
            {"tower_id": "T3", "latitude": 12.9700, "longitude": 77.6000},
            # Tower far away
            {"tower_id": "T4", "latitude": 13.5000, "longitude": 78.0000},
            # Tower with missing coords
            {"tower_id": "T5", "latitude": None, "longitude": None},
        ]

    def test_calculate_radius_density(self, towers):
        # Around T1 (12.9716, 77.5946)
        # Distance T1-T2 is ~600m
        # Distance T1-T3 is ~600m
        # Distance T1-T4 is ~70km
        count_1km = calculate_radius_density(12.9716, 77.5946, towers, 1000.0)
        assert count_1km == 3  # T1, T2, T3 are within 1km

        count_100m = calculate_radius_density(12.9716, 77.5946, towers, 100.0)
        assert count_100m == 1  # Only T1 itself

        count_100km = calculate_radius_density(12.9716, 77.5946, towers, 100000.0)
        assert (
            count_100km == 4
        )  # T1, T2, T3, T4 (T5 is ignored because coords are None)

    def test_calculate_neighbor_density(self, towers):
        neighbor_densities = calculate_neighbor_density(towers, 1000.0)
        assert neighbor_densities["T1"] == 3
        assert neighbor_densities["T2"] == 2
        assert neighbor_densities["T3"] == 2
        assert neighbor_densities["T4"] == 1
        assert neighbor_densities["T5"] == 0

    def test_calculate_grid_density(self, towers):
        # With grid_size_deg=0.01:
        # T1 (12.9716, 77.5946) -> cell (12.97, 77.59)
        # T2 (12.9750, 77.5900) -> cell (12.98, 77.59)
        # T3 (12.9700, 77.6000) -> cell (12.97, 77.60)
        grid = calculate_grid_density(towers, 0.01)
        # Check cell representation and counts
        assert (12.97, 77.59) in grid
        assert grid[(12.97, 77.59)] == 1
        assert (12.98, 77.59) in grid
        assert grid[(12.98, 77.59)] == 1

        # With grid_size_deg=0.1:
        # T1, T2, T3 will round to (13.0, 77.6)
        grid_large = calculate_grid_density(towers, 0.1)
        assert (13.0, 77.6) in grid_large
        assert grid_large[(13.0, 77.6)] == 3

    def test_normalize_densities(self):
        densities = {"T1": 3, "T2": 3, "T3": 1, "T4": 5}
        norm = normalize_densities(densities)
        # min is 1, max is 5. range is 4.
        # T1: (3-1)/4 = 0.5
        # T2: (3-1)/4 = 0.5
        # T3: (1-1)/4 = 0.0
        # T4: (5-1)/4 = 1.0
        assert norm["T1"] == 0.5
        assert norm["T2"] == 0.5
        assert norm["T3"] == 0.0
        assert norm["T4"] == 1.0

    def test_normalize_densities_equal(self):
        densities = {"T1": 3, "T2": 3}
        norm = normalize_densities(densities)
        # max == min, should return 1.0 for all
        assert norm["T1"] == 1.0
        assert norm["T2"] == 1.0

    def test_normalize_densities_empty(self):
        assert normalize_densities({}) == {}
