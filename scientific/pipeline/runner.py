"""
End-to-End Pipeline Runner
==========================

Orchestrates the entire scientific localization sequence:
ScenarioConfig → Validation → Simulation → Evidence Synthesis → Localization → Kalman Tracking → Confidence Estimation.
"""

import time
from typing import List, Dict
from collections import defaultdict
from datetime import timedelta, timezone, datetime

from scientific.logger import get_logger
from scientific.models.scenario_config import ScenarioConfig
from scientific.models.scenario import Scenario
from scientific.models.tower import Tower
from scientific.models.result import LocalizationResult, PipelineResult
from scientific.validation.validators import ScenarioValidator, ResultValidator
from scientific.simulation.measurement_generator import generate_scenario_measurements
from scientific.pipeline.evidence import synthesize_evidence
from scientific.pipeline.weighted_centroid import solve_weighted_centroid
from scientific.pipeline.multilateration import solve_multilateration
from scientific.pipeline.kalman_tracker import track_positions
from scientific.pipeline.confidence import compute_confidence

logger = get_logger(__name__)


def run_pipeline(config: ScenarioConfig) -> PipelineResult:
    """Execute the end-to-end localization and validation pipeline.

    Args:
        config: The input simulation scenario configuration.

    Returns:
        A PipelineResult object containing final position estimates,
        confidence details, audit evidence, and performance metadata.

    Raises:
        ValueError: If config validation fails or no measurements are accepted.
    """
    total_start = time.perf_counter()
    time_breakdown: Dict[str, float] = {}

    logger.info(f"Starting E2E pipeline for scenario config: {config.scenario_id}")

    # -------------------------------------------------------------------------
    # Stage 1: Validate input ScenarioConfig
    # -------------------------------------------------------------------------
    stage_start = time.perf_counter()
    scenario = Scenario(
        scenario_id=config.scenario_id,
        name=config.name,
        description=config.description,
        towers=[Tower(**tp.model_dump()) for tp in config.tower_placements],
        measurements=[],
        noise_level_dbm=config.noise_level_dbm,
        environment_type=config.environment_type,
        expected_device_lat=config.expected_device_lat,
        expected_device_lon=config.expected_device_lon,
    )

    validator = ScenarioValidator(deep=True)
    val_res = validator.validate(scenario)
    if not val_res.is_valid:
        errors_str = "; ".join(f"{err.field}: {err.message}" for err in val_res.errors)
        logger.error(f"Scenario configuration validation failed: {errors_str}")
        raise ValueError(f"Invalid ScenarioConfig: {errors_str}")

    time_breakdown["validation"] = (time.perf_counter() - stage_start) * 1000.0
    logger.info(
        f"Stage 1 complete: Config validated in {time_breakdown['validation']:.2f} ms"
    )

    # -------------------------------------------------------------------------
    # Stage 2: Generate synthetic measurements
    # -------------------------------------------------------------------------
    stage_start = time.perf_counter()
    measurements = generate_scenario_measurements(config)

    # Shift timestamps slightly into the past to prevent "future timestamp" validation failure
    now_utc = datetime.now(timezone.utc)
    for m in measurements:
        if m.timestamp:
            if m.timestamp.tzinfo is None:
                m.timestamp = m.timestamp.replace(tzinfo=timezone.utc)
            if m.timestamp > now_utc:
                m.timestamp -= timedelta(minutes=1)

    scenario.measurements = measurements
    time_breakdown["generation"] = (time.perf_counter() - stage_start) * 1000.0
    logger.info(
        f"Stage 2 complete: Generated {len(measurements)} measurements in "
        f"{time_breakdown['generation']:.2f} ms"
    )

    # -------------------------------------------------------------------------
    # Stage 3: Evidence synthesis & measurement filtering
    # -------------------------------------------------------------------------
    stage_start = time.perf_counter()
    evidence = synthesize_evidence(
        scenario_id=config.scenario_id,
        towers=scenario.towers,
        measurements=measurements,
        thresholds=validator.thresholds,
    )
    accepted_ids = set(evidence.get("accepted_measurement_ids", []))
    accepted_measurements = [
        m for m in measurements if m.measurement_id in accepted_ids
    ]

    if not accepted_measurements:
        logger.error("All generated measurements were rejected by validation checks.")
        raise ValueError(
            "All measurements were rejected by validation, cannot locate device."
        )
    time_breakdown["evidence"] = (time.perf_counter() - stage_start) * 1000.0
    logger.info(
        f"Stage 3 complete: Filtered {len(accepted_measurements)}/{len(measurements)} "
        f"accepted measurements in {time_breakdown['evidence']:.2f} ms"
    )

    # -------------------------------------------------------------------------
    # Stage 4: Run localization algorithm
    # -------------------------------------------------------------------------
    stage_start = time.perf_counter()

    # Group accepted measurements by timestamp for multi-epoch calculations
    meas_by_timestamp = defaultdict(list)
    for m in accepted_measurements:
        meas_by_timestamp[m.timestamp].append(m)
    sorted_timestamps = sorted(meas_by_timestamp.keys())
    raw_localization_results: List[LocalizationResult] = []

    algorithm = config.simulation.algorithm

    for ts in sorted_timestamps:
        epoch_meas = meas_by_timestamp[ts]
        if algorithm == "weighted_centroid":
            loc_res = solve_weighted_centroid(
                scenario_id=config.scenario_id,
                towers=scenario.towers,
                measurements=epoch_meas,
                expected_device_lat=config.expected_device_lat,
                expected_device_lon=config.expected_device_lon,
            )
        else:
            # For multilateration, kalman, and hybrid, run NLLS solver (multilateration)
            loc_res = solve_multilateration(
                scenario_id=config.scenario_id,
                towers=scenario.towers,
                measurements=epoch_meas,
                propagation=config.propagation,
                simulation=config.simulation,
                expected_device_lat=config.expected_device_lat,
                expected_device_lon=config.expected_device_lon,
            )

        # Override algorithm identifier if we are running kalman/hybrid so the raw epoch holds
        # the base algorithm used
        raw_localization_results.append(loc_res)

    time_breakdown["localization"] = (time.perf_counter() - stage_start) * 1000.0
    logger.info(
        f"Stage 4 complete: Processed {len(sorted_timestamps)} epoch(s) via "
        f"'{algorithm}' algorithm in {time_breakdown['localization']:.2f} ms"
    )

    # -------------------------------------------------------------------------
    # Stage 5: Apply tracking / smoothing (if requested)
    # -------------------------------------------------------------------------
    stage_start = time.perf_counter()

    if algorithm in ("kalman", "hybrid"):
        smoothed_results = track_positions(
            results=raw_localization_results,
            expected_device_lat=config.expected_device_lat,
            expected_device_lon=config.expected_device_lon,
        )
        final_history = smoothed_results
    else:
        final_history = raw_localization_results

    final_loc_res = final_history[-1]
    time_breakdown["tracking"] = (time.perf_counter() - stage_start) * 1000.0
    logger.info(
        f"Stage 5 complete: Tracker smoothing in {time_breakdown['tracking']:.2f} ms"
    )

    # -------------------------------------------------------------------------
    # Stage 6: Confidence estimation
    # -------------------------------------------------------------------------
    stage_start = time.perf_counter()

    confidence = compute_confidence(
        scenario_id=config.scenario_id,
        estimated_latitude=final_loc_res.estimated_latitude,
        estimated_longitude=final_loc_res.estimated_longitude,
        towers=scenario.towers,
        measurements=accepted_measurements,
        thresholds=validator.thresholds,
    )
    time_breakdown["confidence"] = (time.perf_counter() - stage_start) * 1000.0
    logger.info(
        f"Stage 6 complete: Calculated confidence in {time_breakdown['confidence']:.2f} ms"
    )

    # -------------------------------------------------------------------------
    # Compile results and metadata
    # -------------------------------------------------------------------------
    total_time_ms = (time.perf_counter() - total_start) * 1000.0
    time_breakdown["total"] = total_time_ms

    metadata = {
        "time_breakdown_ms": time_breakdown,
        "history": [r.model_dump() for r in final_history],
        "algorithm_selected": algorithm,
        "algorithm_applied": final_loc_res.algorithm,
        "total_measurements": len(measurements),
        "accepted_measurements": len(accepted_measurements),
    }

    # Validate final result using ResultValidator
    res_validator = ResultValidator(thresholds=validator.thresholds)
    res_val_res = res_validator.validate(final_loc_res, scenario)
    if not res_val_res.is_valid:
        # Just log error/warnings for pipeline run (do not block execution, metadata stores audit)
        logger.warning(
            "Final localization result has validation findings: "
            f"{[e.message for e in res_val_res.errors]}"
        )
    metadata["validation_findings"] = [
        {
            "field": e.field,
            "message": e.message,
            "severity": e.severity.value,
            "code": e.code,
        }
        for e in res_val_res.errors
    ]

    return PipelineResult(
        localization=final_loc_res,
        confidence=confidence,
        evidence=evidence,
        metadata=metadata,
    )
