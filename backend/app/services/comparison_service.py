from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.case import Case
from app.models.movement_event import MovementEvent
from app.models.confidence_result import ConfidenceResult
from app.schemas.comparison import CaseComparisonResponse, CaseComparisonMetrics

class ComparisonService:
    @staticmethod
    def compare_cases(db: Session, case_ids: list[int]) -> CaseComparisonResponse:
        if len(case_ids) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least two case IDs are required for comparison."
            )
        
        # Verify all cases exist
        cases = db.query(Case).filter(Case.id.in_(case_ids)).all()
        found_case_ids = {c.id for c in cases}
        missing_ids = set(case_ids) - found_case_ids
        if missing_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cases not found: {', '.join(map(str, missing_ids))}"
            )
        
        metrics_list = []
        case_cgis_map = {}
        
        for case_id in case_ids:
            # Distance
            total_distance = db.query(func.sum(MovementEvent.distance_from_prev_m)).filter(
                MovementEvent.case_id == case_id
            ).scalar() or 0.0
            
            # Confidence
            avg_confidence = db.query(func.avg(ConfidenceResult.confidence_score)).filter(
                ConfidenceResult.case_id == case_id
            ).scalar() or 0.0
            
            # CGIs
            movement_events = db.query(MovementEvent.from_cgi, MovementEvent.to_cgi).filter(
                MovementEvent.case_id == case_id
            ).all()
            
            cgis = set()
            for ev in movement_events:
                if ev.from_cgi:
                    cgis.add(ev.from_cgi)
                if ev.to_cgi:
                    cgis.add(ev.to_cgi)
            
            case_cgis_map[case_id] = cgis
            
            metrics_list.append(CaseComparisonMetrics(
                case_id=case_id,
                total_distance_m=float(total_distance),
                average_confidence=float(avg_confidence),
                validation_pass_rate=None  # Placeholder for future validation integration
            ))
            
        # Overlapping towers
        if not case_cgis_map:
            overlapping_towers = set()
        else:
            overlapping_towers = set.intersection(*case_cgis_map.values())
        
        # Max distance diff
        distances = [m.total_distance_m for m in metrics_list]
        max_dist_diff = max(distances) - min(distances) if distances else 0.0
        
        return CaseComparisonResponse(
            cases=metrics_list,
            overlapping_towers=list(overlapping_towers),
            max_distance_difference_m=max_dist_diff
        )
