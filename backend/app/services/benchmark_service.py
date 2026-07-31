from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.case import Case
from app.models.cdr_record import CDRRecord
from app.models.localization_result import LocalizationResult
from app.models.measurement import Measurement
from app.models.tracking_result import TrackingResult
from app.schemas.benchmark import BenchmarkMetric, BenchmarkResponse
from app.schemas.validation import MeasurementInput
from app.services.validation_service import validate_measurements_batch


class BenchmarkService:
    @staticmethod
    def calculate_benchmarks(case_id: int, db: Session) -> BenchmarkResponse:
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        # 1. Validation Pass Rate
        measurements = (
            db.query(Measurement).filter(Measurement.case_id == case_id).all()
        )
        if measurements:
            m_inputs = [
                MeasurementInput(
                    measurement_id=m.measurement_code,
                    tower_id="UNKNOWN",  # Not stored in Measurement
                    timestamp=m.timestamp.isoformat(),
                    rssi_dbm=m.rssi_dbm,
                    latitude=m.latitude,
                    longitude=m.longitude,
                    timing_advance=m.timing_advance,
                    uncertainty_m=m.uncertainty_m,
                )
                for m in measurements
            ]
            val_res = validate_measurements_batch(m_inputs)
            validation_pass_rate = (val_res.valid_count / len(measurements)) * 100.0
        else:
            validation_pass_rate = 100.0

        # 2. Tower Resolution Rate & Unknown Tower Percentage
        total_cdrs = (
            db.query(func.count(CDRRecord.id))
            .filter(CDRRecord.case_id == case_id)
            .scalar()
            or 0
        )
        if total_cdrs > 0:
            resolved_cdrs = (
                db.query(func.count(CDRRecord.id))
                .filter(CDRRecord.case_id == case_id, CDRRecord.latitude.isnot(None))
                .scalar()
                or 0
            )
            tower_resolution_rate = (resolved_cdrs / total_cdrs) * 100.0
            unknown_tower_percentage = 100.0 - tower_resolution_rate
        else:
            tower_resolution_rate = 100.0
            unknown_tower_percentage = 0.0

        # 3. Kalman Improvement Factor
        avg_loc_error = (
            db.query(func.avg(LocalizationResult.error_m))
            .filter(LocalizationResult.case_id == case_id)
            .scalar()
            or 0.0
        )

        avg_track_error = (
            db.query(func.avg(TrackingResult.error_m))
            .filter(TrackingResult.case_id == case_id)
            .scalar()
            or 0.0
        )

        if avg_track_error > 0:
            kalman_improvement_factor = float(avg_loc_error / avg_track_error)
        else:
            kalman_improvement_factor = 1.0 if avg_loc_error == 0 else 10.0

        metrics = []

        metrics.append(
            BenchmarkMetric(
                metric_name="Validation Pass Rate",
                value=round(validation_pass_rate, 2),
                threshold=settings.benchmark_min_validation_pass_rate,
                passed=validation_pass_rate
                >= settings.benchmark_min_validation_pass_rate,
            )
        )

        metrics.append(
            BenchmarkMetric(
                metric_name="Tower Resolution Rate",
                value=round(tower_resolution_rate, 2),
                threshold=settings.benchmark_min_tower_resolution_rate,
                passed=tower_resolution_rate
                >= settings.benchmark_min_tower_resolution_rate,
            )
        )

        metrics.append(
            BenchmarkMetric(
                metric_name="Unknown Tower Percentage",
                value=round(unknown_tower_percentage, 2),
                threshold=settings.benchmark_max_unknown_tower_percentage,
                passed=unknown_tower_percentage
                <= settings.benchmark_max_unknown_tower_percentage,
            )
        )

        metrics.append(
            BenchmarkMetric(
                metric_name="Kalman Improvement Factor",
                value=round(kalman_improvement_factor, 2),
                threshold=settings.benchmark_min_kalman_improvement_factor,
                passed=kalman_improvement_factor
                >= settings.benchmark_min_kalman_improvement_factor,
            )
        )

        case_passed = all(m.passed for m in metrics)

        return BenchmarkResponse(case_passed=case_passed, metrics=metrics)
