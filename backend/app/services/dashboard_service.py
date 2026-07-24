"""Dashboard Service
=================

Provides case-wide aggregated metrics, tower confidence breakdowns, movement stats,
localization & tracking summaries, and pipeline health status for investigation dashboards.
"""

from app.models.case import Case
from app.models.cdr_record import CDRRecord
from app.models.confidence_result import ConfidenceResult
from app.models.localization_result import LocalizationResult
from app.models.measurement import Measurement
from app.models.movement_event import MovementEvent
from app.models.tower import Tower
from app.models.tracking_result import TrackingResult
from app.schemas.dashboard import (
    CDRSummary,
    CaseSummaryInfo,
    ConfidenceSummary,
    DashboardSummary,
    LatestConfidence,
    LatestLocalization,
    LatestTrackingStep,
    LocalizationSummary,
    MovementSummary,
    PipelineHealthStatus,
    TowerSummary,
    TrackingSummary,
)
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session


class DashboardService:
    """Service to handle case aggregation metrics for dashboard visualization."""

    @staticmethod
    def get_case_summary(db: Session, case_id: int) -> DashboardSummary:
        """Fetch and calculate all aggregated summary metrics for a given case."""
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise HTTPException(
                status_code=404, detail=f"Case with ID {case_id} not found"
            )

        # 1. Case Summary Info
        case_info = CaseSummaryInfo.model_validate(case)

        # 2. CDR Records & Measurements Summary
        total_cdr = (
            db.query(func.count(CDRRecord.id))
            .filter(CDRRecord.case_id == case_id)
            .scalar()
            or 0
        )
        total_measurements = (
            db.query(func.count(Measurement.id))
            .filter(Measurement.case_id == case_id)
            .scalar()
            or 0
        )

        op_rows = (
            db.query(CDRRecord.operator, func.count(CDRRecord.id))
            .filter(CDRRecord.case_id == case_id)
            .group_by(CDRRecord.operator)
            .all()
        )
        operator_breakdown = {op: count for op, count in op_rows if op}

        type_rows = (
            db.query(CDRRecord.call_type, func.count(CDRRecord.id))
            .filter(CDRRecord.case_id == case_id)
            .group_by(CDRRecord.call_type)
            .all()
        )
        call_type_breakdown = {ct: count for ct, count in type_rows if ct}

        min_ts, max_ts = db.query(
            func.min(CDRRecord.timestamp), func.max(CDRRecord.timestamp)
        ).filter(CDRRecord.case_id == case_id).first() or (None, None)

        target_nums = [
            r[0]
            for r in db.query(CDRRecord.target_number)
            .filter(CDRRecord.case_id == case_id, CDRRecord.target_number.isnot(None))
            .distinct()
            .all()
        ]
        imeis = [
            r[0]
            for r in db.query(CDRRecord.imei)
            .filter(CDRRecord.case_id == case_id, CDRRecord.imei.isnot(None))
            .distinct()
            .all()
        ]
        imsis = [
            r[0]
            for r in db.query(CDRRecord.imsi)
            .filter(CDRRecord.case_id == case_id, CDRRecord.imsi.isnot(None))
            .distinct()
            .all()
        ]

        cdr_summary = CDRSummary(
            total_records=total_cdr,
            total_measurements=total_measurements,
            operator_breakdown=operator_breakdown,
            call_type_breakdown=call_type_breakdown,
            earliest_timestamp=min_ts,
            latest_timestamp=max_ts,
            target_numbers=target_nums,
            imeis=imeis,
            imsis=imsis,
        )

        # 3. Tower Summary
        cgis_first = [
            r[0]
            for r in db.query(CDRRecord.first_cgi)
            .filter(CDRRecord.case_id == case_id, CDRRecord.first_cgi.isnot(None))
            .distinct()
            .all()
        ]
        cgis_last = [
            r[0]
            for r in db.query(CDRRecord.last_cgi)
            .filter(CDRRecord.case_id == case_id, CDRRecord.last_cgi.isnot(None))
            .distinct()
            .all()
        ]
        all_cgis = list(set(cgis_first + cgis_last))

        known_count = 0
        estimated_count = 0
        unknown_count = 0

        if all_cgis:
            towers = db.query(Tower).filter(Tower.cgi.in_(all_cgis)).all()
            found_cgis = {t.cgi for t in towers if t.cgi}
            missing_cgis_count = len(all_cgis) - len(found_cgis)

            for t in towers:
                if t.confidence_category == "Known" or (
                    t.latitude is not None
                    and t.longitude is not None
                    and t.confidence_category != "Estimated"
                ):
                    known_count += 1
                elif t.confidence_category == "Estimated":
                    estimated_count += 1
                else:
                    unknown_count += 1

            unknown_count += missing_cgis_count
        else:
            # Check direct towers table if any towers registered with operator/matching
            towers = db.query(Tower).all()
            # If no CGIs in CDRs, towers summary stays zeroed

        tower_summary = TowerSummary(
            total_towers=len(all_cgis),
            known_coords_count=known_count,
            estimated_coords_count=estimated_count,
            unknown_coords_count=unknown_count,
        )

        # 4. Movement Summary
        total_mov_events = (
            db.query(func.count(MovementEvent.id))
            .filter(MovementEvent.case_id == case_id)
            .scalar()
            or 0
        )
        handover_events = (
            db.query(func.count(MovementEvent.id))
            .filter(
                MovementEvent.case_id == case_id, MovementEvent.event_type == "handover"
            )
            .scalar()
            or 0
        )
        total_dist_m = (
            db.query(func.sum(MovementEvent.distance_from_prev_m))
            .filter(MovementEvent.case_id == case_id)
            .scalar()
            or 0.0
        )
        max_speed = (
            db.query(func.max(MovementEvent.speed_kmh))
            .filter(MovementEvent.case_id == case_id)
            .scalar()
            or 0.0
        )
        avg_speed = (
            db.query(func.avg(MovementEvent.speed_kmh))
            .filter(MovementEvent.case_id == case_id)
            .scalar()
            or 0.0
        )

        movement_summary = MovementSummary(
            total_events=total_mov_events,
            handover_events=handover_events,
            total_distance_km=round(total_dist_m / 1000.0, 3),
            max_speed_kmh=round(max_speed, 2),
            avg_speed_kmh=round(avg_speed, 2),
        )

        # 5. Localization Summary
        loc_count = (
            db.query(func.count(LocalizationResult.id))
            .filter(LocalizationResult.case_id == case_id)
            .scalar()
            or 0
        )
        latest_loc_obj = (
            db.query(LocalizationResult)
            .filter(LocalizationResult.case_id == case_id)
            .order_by(
                LocalizationResult.created_at.desc(), LocalizationResult.id.desc()
            )
            .first()
        )
        latest_loc = (
            LatestLocalization(
                id=latest_loc_obj.id,
                algorithm=latest_loc_obj.algorithm,
                estimated_latitude=latest_loc_obj.estimated_latitude,
                estimated_longitude=latest_loc_obj.estimated_longitude,
                error_m=latest_loc_obj.error_m,
                computation_time_ms=latest_loc_obj.computation_time_ms,
                signals_used=latest_loc_obj.signals_used,
            )
            if latest_loc_obj
            else None
        )
        localization_summary = LocalizationSummary(
            total_results=loc_count,
            latest_result=latest_loc,
        )

        # 6. Tracking Summary
        track_count = (
            db.query(func.count(TrackingResult.id))
            .filter(TrackingResult.case_id == case_id)
            .scalar()
            or 0
        )
        latest_track_obj = (
            db.query(TrackingResult)
            .filter(TrackingResult.case_id == case_id)
            .order_by(TrackingResult.step_number.desc(), TrackingResult.id.desc())
            .first()
        )
        latest_track = (
            LatestTrackingStep(
                step_number=latest_track_obj.step_number,
                smoothed_latitude=latest_track_obj.smoothed_latitude,
                smoothed_longitude=latest_track_obj.smoothed_longitude,
                velocity_mps=latest_track_obj.velocity_mps,
                heading_deg=latest_track_obj.heading_deg,
                algorithm=latest_track_obj.algorithm,
                timestamp=latest_track_obj.timestamp,
            )
            if latest_track_obj
            else None
        )
        tracking_summary = TrackingSummary(
            total_steps=track_count,
            latest_step=latest_track,
        )

        # 7. Confidence Summary
        latest_conf_obj = (
            db.query(ConfidenceResult)
            .filter(ConfidenceResult.case_id == case_id)
            .order_by(ConfidenceResult.created_at.desc(), ConfidenceResult.id.desc())
            .first()
        )
        latest_conf = (
            LatestConfidence(
                confidence_score=latest_conf_obj.confidence_score,
                confidence_level=latest_conf_obj.confidence_level,
                gdop=latest_conf_obj.gdop,
                method=latest_conf_obj.method,
            )
            if latest_conf_obj
            else None
        )
        confidence_summary = ConfidenceSummary(latest_result=latest_conf)

        # 8. Pipeline Health Status
        has_imported = total_cdr > 0 or total_measurements > 0
        has_towers = tower_summary.total_towers > 0
        has_movement = total_mov_events > 0
        has_loc = loc_count > 0
        has_conf = latest_conf is not None

        pipeline_status = PipelineHealthStatus(
            imported=has_imported,
            validated=has_imported,
            towers_resolved=has_towers,
            movement_reconstructed=has_movement,
            localization_complete=has_loc,
            confidence_generated=has_conf,
            evidence_logged=has_loc and has_conf,
            report_ready=has_loc and has_conf,
        )

        return DashboardSummary(
            case=case_info,
            cdr=cdr_summary,
            towers=tower_summary,
            movement=movement_summary,
            localization=localization_summary,
            tracking=tracking_summary,
            confidence=confidence_summary,
            pipeline_status=pipeline_status,
        )
