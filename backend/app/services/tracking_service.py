"""
Tracking Service
=================

Orchestrates the Kalman filter tracking pipeline:
  DB localization results → scientific tracker → persisted tracking path.
"""

import math
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.tracking_result import TrackingResult as TrackingResultORM
from app.repositories.tracking_repository import TrackingRepository
from app.repositories.localization_repository import LocalizationRepository
from app.repositories.case_repository import CaseRepository
from app.shared.validation import ValidationError, decode_case_code

from scientific.constants import haversine_distance_m, METERS_PER_DEGREE_LAT
from scientific.models.result import LocalizationResult as ScientificResult
from scientific.models.scenario_config import ScenarioConfig
from scientific.pipeline.kalman_tracker import track_positions


class TrackingService:
    """Service that bridges DB localization results → Kalman smoother → persisted tracks."""

    @staticmethod
    def run_tracking(
        db: Session,
        case_code: str,
    ) -> Dict:
        """Run Kalman-smoothed tracking over stored localization results for a case.

        1. Decode case_code → load case + scenario
        2. Load scenario config for ground-truth coordinates
        3. Retrieve stored localization results for the case
        4. Convert DB models → scientific LocalizationResult models
        5. Call track_positions() from the scientific pipeline
        6. Persist each smoothed step as TrackingResult rows
        7. Return structured response data

        Returns:
            Dictionary with case_code, total_steps, path, distance_km,
            avg_velocity_kmh, computation_time_ms.
        """
        overall_start = time.perf_counter()

        # 1. Decode case code and load case
        case_id = decode_case_code(case_code)
        case = CaseRepository.get(db, case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        if not case.scenario_id:
            raise ValidationError(
                "case",
                "Case must have an associated scenario to run tracking.",
                status_code=400,
            )

        # 2. Load scenario config for ground-truth coords
        expected_lat, expected_lon = TrackingService._load_ground_truth(
            case.scenario_id
        )

        # 3. Retrieve stored localization results for the case
        db_loc_results = LocalizationRepository.get_by_case(db, case_id)
        if not db_loc_results or len(db_loc_results) < 2:
            raise ValidationError(
                "localization_results",
                "At least 2 localization results are required to run tracking. "
                f"Found {len(db_loc_results) if db_loc_results else 0}.",
                status_code=400,
            )

        # 4. Convert DB ORM models → scientific Pydantic models
        scientific_results: List[ScientificResult] = []
        for loc in db_loc_results:
            scientific_results.append(
                ScientificResult(
                    scenario_id=f"SCN-{loc.scenario_id:03d}" if loc.scenario_id else "SCN-000",
                    algorithm=loc.algorithm,
                    estimated_latitude=loc.estimated_latitude,
                    estimated_longitude=loc.estimated_longitude,
                    error_m=loc.error_m,
                    computation_time_ms=loc.computation_time_ms,
                    signals_used=3,  # default if not stored
                    timestamp=loc.created_at or datetime.now(timezone.utc),
                )
            )

        # 5. Call the Kalman smoother
        smoothed = track_positions(
            results=scientific_results,
            expected_device_lat=expected_lat,
            expected_device_lon=expected_lon,
        )

        # 6. Delete previous tracking results for this case, then persist new ones
        TrackingRepository.delete_by_case(db, case_id)

        tracking_rows: List[TrackingResultORM] = []
        for i, sr in enumerate(smoothed):
            # Compute heading from velocity components
            v_lat = getattr(sr, "velocity_lat", 0.0)
            v_lon = getattr(sr, "velocity_lon", 0.0)
            heading = TrackingService._compute_heading(v_lat, v_lon)

            # Compute speed in m/s
            v_lat_mps = getattr(sr, "velocity_lat_mps", 0.0)
            v_lon_mps = getattr(sr, "velocity_lon_mps", 0.0)
            speed_mps = math.sqrt(v_lat_mps**2 + v_lon_mps**2)

            row = TrackingResultORM(
                case_id=case_id,
                step_number=i + 1,
                smoothed_latitude=sr.estimated_latitude,
                smoothed_longitude=sr.estimated_longitude,
                velocity_lat=v_lat,
                velocity_lon=v_lon,
                velocity_mps=speed_mps,
                heading_deg=heading,
                error_m=sr.error_m,
                computation_time_ms=sr.computation_time_ms,
                algorithm=sr.algorithm,
                timestamp=sr.timestamp,
            )
            tracking_rows.append(row)

        TrackingRepository.bulk_create(db, tracking_rows)

        # 7. Build response
        overall_ms = (time.perf_counter() - overall_start) * 1000.0

        path = []
        total_distance_m = 0.0
        velocities_kmh: List[float] = []

        for i, row in enumerate(tracking_rows):
            speed_kmh = (row.velocity_mps or 0.0) * 3.6
            velocities_kmh.append(speed_kmh)

            if i > 0:
                prev = tracking_rows[i - 1]
                total_distance_m += haversine_distance_m(
                    prev.smoothed_latitude,
                    prev.smoothed_longitude,
                    row.smoothed_latitude,
                    row.smoothed_longitude,
                )

            path.append(
                {
                    "step_number": row.step_number,
                    "latitude": row.smoothed_latitude,
                    "longitude": row.smoothed_longitude,
                    "velocity_kmh": round(speed_kmh, 2),
                    "timestamp": row.timestamp.isoformat() if row.timestamp else None,
                    "heading_deg": round(row.heading_deg, 1) if row.heading_deg is not None else None,
                }
            )

        avg_vel = sum(velocities_kmh) / len(velocities_kmh) if velocities_kmh else 0.0

        return {
            "case_code": case_code.upper(),
            "total_steps": len(tracking_rows),
            "path": path,
            "distance_km": round(total_distance_m / 1000.0, 4),
            "avg_velocity_kmh": round(avg_vel, 2),
            "computation_time_ms": round(overall_ms, 2),
        }

    @staticmethod
    def _load_ground_truth(scenario_id: int) -> Tuple[Optional[float], Optional[float]]:
        """Load expected device coordinates from the scenario dataset."""
        dataset_path = (
            Path(__file__).resolve().parents[3]
            / "datasets"
            / "sample"
            / "scenario_example.json"
        )
        if not dataset_path.exists():
            return None, None

        try:
            with open(dataset_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for cfg_dict in data.get("scenario_configs", []):
                sc_id_str = cfg_dict.get("scenario_id", "")
                try:
                    cfg_id_int = int(sc_id_str.split("-")[-1])
                except (ValueError, IndexError):
                    continue
                if cfg_id_int == scenario_id:
                    return (
                        cfg_dict.get("expected_device_lat"),
                        cfg_dict.get("expected_device_lon"),
                    )
        except Exception:
            pass

        return None, None

    @staticmethod
    def _compute_heading(v_lat: float, v_lon: float) -> Optional[float]:
        """Compute bearing in degrees [0, 360) from velocity components.

        Uses atan2(v_lon, v_lat) to get heading where 0° = North, 90° = East.
        Returns None if velocity is essentially zero.
        """
        if abs(v_lat) < 1e-12 and abs(v_lon) < 1e-12:
            return None
        heading = math.degrees(math.atan2(v_lon, v_lat))
        if heading < 0:
            heading += 360.0
        return heading
