"""
Scenario Validator
==================
"""

from __future__ import annotations

import math
from datetime import datetime

from scientific.config import (
    DEFAULT_VALIDATION_THRESHOLDS,
    ValidationThresholds,
    get_environment_config,
)
from scientific.constants import TA_RESOLUTION_M
from scientific.models.measurement import Measurement
from scientific.models.scenario import Scenario
from scientific.models.tower import Tower
from scientific.validation.measurement_validator import MeasurementValidator
from scientific.validation.tower_validator import TowerValidator
from scientific.validation.types import Severity, ValidationError, ValidationResult


class ScenarioValidator:
    """Validates a complete :class:`Scenario` instance.

    Checks performed:
        1. Required fields presence.
        2. All tower IDs must be unique within the scenario.
        3. Every measurement must reference a tower that exists in the
           scenario's tower list.
        4. Unique measurement IDs and duplicate record checks (same tower + timestamp).
        5. If ground-truth coordinates are provided, both lat and lon
           must be present, and must fall within expected operational areas.
        6. At least one measurement should exist for each tower
           (warning if a tower has zero coverage).
        7. Physics consistency cross-checks between Timing Advance distance and RSSI decay models.
        8. All embedded towers and measurements pass their own
           validators (deep validation).

    Parameters:
        deep: If ``True`` (default), also runs :class:`TowerValidator`
              and :class:`MeasurementValidator` on each embedded object.
    """

    def __init__(
        self,
        *,
        deep: bool = True,
        thresholds: ValidationThresholds = DEFAULT_VALIDATION_THRESHOLDS,
    ) -> None:
        self._deep = deep
        self.thresholds = thresholds
        self._tower_validator = TowerValidator(thresholds=thresholds)
        self._measurement_validator = MeasurementValidator(thresholds=thresholds)

    def validate(self, scenario: Scenario) -> ValidationResult:
        """Run all scenario validation checks."""
        result = ValidationResult()

        # --- 1. Missing scenario values ---
        if not scenario.scenario_id or scenario.scenario_id.strip() == "":
            result.errors.append(
                ValidationError(
                    field="scenario_id",
                    message="Scenario ID must be provided and cannot be empty.",
                    code="SCENARIO_MISSING_ID",
                )
            )
        if not scenario.name or scenario.name.strip() == "":
            result.errors.append(
                ValidationError(
                    field="name",
                    message="Scenario name must be provided and cannot be empty.",
                    code="SCENARIO_MISSING_NAME",
                )
            )
        if scenario.towers is None or len(scenario.towers) < 3:
            result.errors.append(
                ValidationError(
                    field="towers",
                    message=(
                        f"At least 3 towers are required for localization. "
                        f"Got {len(scenario.towers) if scenario.towers else 0}."
                    ),
                    code="SCENARIO_INSUFFICIENT_TOWERS",
                )
            )

        # --- 2. Unique tower IDs ---
        tower_ids = (
            [t.tower_id for t in scenario.towers if t.tower_id]
            if scenario.towers
            else []
        )
        seen_towers: set[str] = set()
        for idx, tid in enumerate(tower_ids):
            if tid in seen_towers:
                result.errors.append(
                    ValidationError(
                        field=f"towers[{idx}].tower_id",
                        message=f"Duplicate tower_id '{tid}' in scenario.",
                        code="SCENARIO_DUPLICATE_TOWER",
                    )
                )
            seen_towers.add(tid)

        # --- 3. Measurement → Tower referential integrity & duplicates ---
        tower_id_set = set(tower_ids)
        seen_meas_ids: set[str] = set()
        seen_meas_records: set[tuple[str, datetime]] = set()

        measurements = scenario.measurements or []
        for idx, m in enumerate(measurements):
            # Check unique measurement IDs
            if m.measurement_id:
                if m.measurement_id in seen_meas_ids:
                    result.errors.append(
                        ValidationError(
                            field=f"measurements[{idx}].measurement_id",
                            message=f"Duplicate measurement_id '{m.measurement_id}' in scenario.",
                            code="SCENARIO_DUPLICATE_MEASUREMENT",
                        )
                    )
                seen_meas_ids.add(m.measurement_id)

            # Referential integrity
            if m.tower_id not in tower_id_set:
                result.errors.append(
                    ValidationError(
                        field=f"measurements[{idx}].tower_id",
                        message=(
                            f"Measurement '{m.measurement_id}' references tower "
                            f"'{m.tower_id}' which is not defined in this scenario."
                        ),
                        code="SCENARIO_ORPHAN_MEASUREMENT",
                    )
                )

            # Check duplicate timestamps (same tower, same timestamp)
            if m.tower_id and m.timestamp:
                record_key = (m.tower_id, m.timestamp)
                if record_key in seen_meas_records:
                    result.errors.append(
                        ValidationError(
                            field=f"measurements[{idx}].timestamp",
                            message=(
                                f"Duplicate measurement record found for tower '{m.tower_id}' "
                                f"at timestamp {m.timestamp.isoformat()}."
                            ),
                            code="SCENARIO_DUPLICATE_RECORD",
                        )
                    )
                seen_meas_records.add(record_key)

        # --- 4. Ground-truth coordinate pairing & bounds checking ---
        has_gt_lat = scenario.expected_device_lat is not None
        has_gt_lon = scenario.expected_device_lon is not None
        if has_gt_lat != has_gt_lon:
            result.errors.append(
                ValidationError(
                    field="expected_device_lat/expected_device_lon",
                    message=(
                        "Ground-truth coordinates must both be provided or both "
                        "be omitted."
                    ),
                    code="SCENARIO_PARTIAL_GROUND_TRUTH",
                )
            )
        elif has_gt_lat and has_gt_lon:
            lat_min, lat_max = self.thresholds.latitude_range
            lon_min, lon_max = self.thresholds.longitude_range
            if not (lat_min <= scenario.expected_device_lat <= lat_max) or not (
                lon_min <= scenario.expected_device_lon <= lon_max
            ):
                result.errors.append(
                    ValidationError(
                        field="expected_device_lat/expected_device_lon",
                        message=(
                            f"Ground-truth coordinates ({scenario.expected_device_lat}, {scenario.expected_device_lon}) "
                            f"are outside the expected operational area. "
                            f"Allowed range: Latitude {self.thresholds.latitude_range}, Longitude {self.thresholds.longitude_range}."
                        ),
                        code="SCENARIO_COORDS_OUT_OF_BOUNDS",
                    )
                )

        # --- 5. Tower coverage (every tower should have ≥1 measurement) ---
        if scenario.measurements:
            referenced_towers = {
                m.tower_id for m in scenario.measurements if m.tower_id
            }
            uncovered = tower_id_set - referenced_towers
            for tid in uncovered:
                result.errors.append(
                    ValidationError(
                        field="towers/measurements",
                        message=(
                            f"Tower '{tid}' has no measurements in this scenario. "
                            "It will not contribute to localization."
                        ),
                        severity=Severity.WARNING,
                        code="SCENARIO_UNCOVERED_TOWER",
                    )
                )

        # --- 6. Physics-based TA vs RSSI decay model cross-check ---
        if scenario.towers and scenario.measurements:
            env_cfg = get_environment_config(scenario.environment_type)
            exponent = env_cfg.path_loss_exponent
            ref_loss = env_cfg.reference_loss_db
            ref_dist = env_cfg.reference_distance_m
            sigma = env_cfg.shadow_fading_std_db

            tower_map = {t.tower_id: t for t in scenario.towers if t.tower_id}

            for idx, m in enumerate(scenario.measurements):
                if m.timing_advance is not None and m.rssi_dbm is not None:
                    tower = tower_map.get(m.tower_id)
                    if tower is not None and tower.transmit_power_dbm is not None:
                        ta = m.timing_advance
                        # Compute distance interval implied by TA
                        d_min = max(ref_dist, (ta - 0.5) * TA_RESOLUTION_M)
                        d_max = max(ref_dist, (ta + 0.5) * TA_RESOLUTION_M)

                        # Compute path loss at the limits
                        loss_min = ref_loss + 10.0 * exponent * math.log10(
                            d_min / ref_dist
                        )
                        loss_max = ref_loss + 10.0 * exponent * math.log10(
                            d_max / ref_dist
                        )

                        expected_rssi_max = tower.transmit_power_dbm - loss_min
                        expected_rssi_min = tower.transmit_power_dbm - loss_max

                        # Define upper and lower bounds with standard deviation margins
                        rssi_upper_bound = expected_rssi_max + 3.0 * sigma
                        rssi_lower_bound = expected_rssi_min - 4.0 * sigma

                        # Check for wild mismatch
                        if m.rssi_dbm > rssi_upper_bound:
                            result.errors.append(
                                ValidationError(
                                    field=f"measurements[{idx}].timing_advance",
                                    message=(
                                        f"Physics Mismatch: Measurement '{m.measurement_id}' has RSSI of {m.rssi_dbm} dBm, "
                                        f"which is physically too strong for the Timing Advance of {ta} "
                                        f"(implied distance range: {d_min:.1f}m - {d_max:.1f}m, expected RSSI range: "
                                        f"{expected_rssi_min:.1f} to {expected_rssi_max:.1f} dBm with shadow fading std {sigma} dB)."
                                    ),
                                    severity=Severity.WARNING,
                                    code="SCENARIO_TA_RSSI_PHYSICS_MISMATCH",
                                )
                            )
                        elif m.rssi_dbm < rssi_lower_bound:
                            result.errors.append(
                                ValidationError(
                                    field=f"measurements[{idx}].timing_advance",
                                    message=(
                                        f"Physics Mismatch: Measurement '{m.measurement_id}' has RSSI of {m.rssi_dbm} dBm, "
                                        f"which is physically too weak for the Timing Advance of {ta} "
                                        f"(implied distance range: {d_min:.1f}m - {d_max:.1f}m, expected RSSI range: "
                                        f"{expected_rssi_min:.1f} to {expected_rssi_max:.1f} dBm with shadow fading std {sigma} dB)."
                                    ),
                                    severity=Severity.WARNING,
                                    code="SCENARIO_TA_RSSI_PHYSICS_MISMATCH",
                                )
                            )

        # --- 7. Deep validation of embedded objects ---
        if self._deep:
            if scenario.towers:
                for idx, tower in enumerate(scenario.towers):
                    sub = self._tower_validator.validate(tower)
                    for err in sub.errors:
                        result.errors.append(
                            ValidationError(
                                field=f"towers[{idx}].{err.field}",
                                message=err.message,
                                severity=err.severity,
                                code=err.code,
                            )
                        )

            if scenario.measurements:
                for idx, meas in enumerate(scenario.measurements):
                    sub = self._measurement_validator.validate(meas)
                    for err in sub.errors:
                        result.errors.append(
                            ValidationError(
                                field=f"measurements[{idx}].{err.field}",
                                message=err.message,
                                severity=err.severity,
                                code=err.code,
                            )
                        )

        return result


def validate_measurement(
    measurement: Measurement,
    thresholds: ValidationThresholds = DEFAULT_VALIDATION_THRESHOLDS,
) -> ValidationResult:
    """Shortcut: validate a single Measurement."""
    return MeasurementValidator(thresholds).validate(measurement)


def validate_tower(
    tower: Tower,
    thresholds: ValidationThresholds = DEFAULT_VALIDATION_THRESHOLDS,
) -> ValidationResult:
    """Shortcut: validate a single Tower."""
    return TowerValidator(thresholds).validate(tower)


def validate_scenario(
    scenario: Scenario,
    *,
    deep: bool = True,
    thresholds: ValidationThresholds = DEFAULT_VALIDATION_THRESHOLDS,
) -> ValidationResult:
    """Shortcut: validate a complete Scenario (optionally with deep checks)."""
    return ScenarioValidator(deep=deep, thresholds=thresholds).validate(scenario)


def validate_batch(
    scenarios: list[Scenario],
    *,
    deep: bool = True,
    thresholds: ValidationThresholds = DEFAULT_VALIDATION_THRESHOLDS,
) -> dict[str, ValidationResult]:
    """Validate a batch of Scenario objects, returning a mapping of scenario_id to ValidationResult."""
    validator = ScenarioValidator(deep=deep, thresholds=thresholds)
    return {s.scenario_id: validator.validate(s) for s in scenarios}
