"""
Evidence Synthesis Engine
=========================

Runs measurement validation and compiles structured audit evidence reports
documenting accepted and rejected measurements, active towers, and specific
rejection reasons.
"""

from typing import List, Dict, Any

from scientific.models.measurement import Measurement
from scientific.models.tower import Tower
from scientific.validation.validators import MeasurementValidator, Severity
from scientific.config import ValidationThresholds, DEFAULT_VALIDATION_THRESHOLDS


def synthesize_evidence(
    scenario_id: str,
    towers: List[Tower],
    measurements: List[Measurement],
    thresholds: ValidationThresholds = DEFAULT_VALIDATION_THRESHOLDS,
) -> Dict[str, Any]:
    """Synthesize audit evidence detailing validated, accepted, and rejected measurements.

    Args:
        scenario_id: Identifier of the source scenario.
        towers: List of tower configurations.
        measurements: List of signal measurements to validate.
        thresholds: Validation thresholds to use for measurement audits.

    Returns:
        A dictionary containing structured audit records.
    """
    validator = MeasurementValidator(thresholds=thresholds)

    accepted_measurements: List[Measurement] = []
    rejected_details: List[Dict[str, Any]] = []

    # Map for counting measurements per tower
    tower_stats: Dict[str, Dict[str, int]] = {
        t.tower_id: {
            "total_measurements": 0,
            "accepted_measurements": 0,
            "rejected_measurements": 0,
        }
        for t in towers if t.tower_id
    }

    # Run validation on each measurement
    for m in measurements:
        tid = m.tower_id
        if not tid:
            continue

        # Initialize stats for tower if it wasn't in towers list but is in measurements
        if tid not in tower_stats:
            tower_stats[tid] = {
                "total_measurements": 0,
                "accepted_measurements": 0,
                "rejected_measurements": 0,
            }

        validation_result = validator.validate(m)
        tower_stats[tid]["total_measurements"] += 1

        if validation_result.is_valid:
            accepted_measurements.append(m)
            tower_stats[tid]["accepted_measurements"] += 1
        else:
            tower_stats[tid]["rejected_measurements"] += 1
            # Extract rejection errors (with ERROR severity)
            errors = [
                {
                    "field": err.field,
                    "message": err.message,
                    "code": err.code,
                    "severity": err.severity.value if hasattr(err.severity, "value") else str(err.severity)
                }
                for err in validation_result.errors
                if err.severity == Severity.ERROR or str(err.severity) == "error"
            ]
            rejected_details.append({
                "measurement_id": m.measurement_id,
                "tower_id": m.tower_id,
                "timestamp": m.timestamp.isoformat() if m.timestamp else None,
                "errors": errors
            })

    # Compile tower info
    towers_list = []
    for t in towers:
        stats = tower_stats.get(t.tower_id, {
            "total_measurements": 0,
            "accepted_measurements": 0,
            "rejected_measurements": 0,
        })
        towers_list.append({
            "tower_id": t.tower_id,
            "latitude": t.latitude,
            "longitude": t.longitude,
            "total_measurements": stats["total_measurements"],
            "accepted_measurements": stats["accepted_measurements"],
            "rejected_measurements": stats["rejected_measurements"],
            "status": "active" if stats["accepted_measurements"] > 0 else "inactive",
        })

    # Calculate summary metrics
    total_count = len(measurements)
    accepted_count = len(accepted_measurements)
    rejected_count = total_count - accepted_count
    active_towers_count = sum(1 for t in towers_list if t["status"] == "active")

    return {
        "scenario_id": scenario_id,
        "summary": {
            "total_measurements": total_count,
            "accepted_measurements": accepted_count,
            "rejected_measurements": rejected_count,
            "towers_total": len(towers),
            "towers_used_count": active_towers_count,
        },
        "towers": towers_list,
        "accepted_measurement_ids": [m.measurement_id for m in accepted_measurements if m.measurement_id],
        "rejections": rejected_details,
    }
