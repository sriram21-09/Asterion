from app.models.case import Case
from app.repositories.case_repository import CaseRepository
from app.repositories.scenario_repository import ScenarioRepository
from app.schemas.case import CaseCreate
from app.shared.validation import (
    ValidationError,
    pagination_offset,
    validate_non_empty_string,
    validate_pagination,
)
from fastapi import HTTPException
from sqlalchemy.orm import Session


class CaseService:
    """Service class for Case business logic and validation.

    # ponytail: simple static class wrapper for business actions
    """

    @staticmethod
    def create_case(db: Session, case_in: CaseCreate) -> Case:
        # Validate title is non-empty and <= 255 chars
        title = validate_non_empty_string(case_in.title, "title", max_length=255)

        # Validate description length if provided
        description = None
        if case_in.description is not None:
            stripped = case_in.description.strip()
            if stripped:
                description = validate_non_empty_string(
                    stripped, "description", max_length=1000
                )

        # Validate scenario_id existence if provided
        if case_in.scenario_id is not None:
            scenario = ScenarioRepository.get(db, scenario_id=case_in.scenario_id)
            if not scenario:
                raise ValidationError(
                    "scenario_id",
                    f"Scenario with ID {case_in.scenario_id} does not exist.",
                    status_code=400,
                )

        return CaseRepository.create(
            db, title=title, description=description, scenario_id=case_in.scenario_id
        )

    @staticmethod
    def get_case(db: Session, case_id: int) -> Case:
        case = CaseRepository.get(db, case_id=case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        return case

    @staticmethod
    def list_cases(
        db: Session, page: int | None = None, page_size: int | None = None
    ) -> list[Case]:
        validated_page, validated_page_size = validate_pagination(page, page_size)
        offset = pagination_offset(validated_page, validated_page_size)
        return CaseRepository.get_multi(db, skip=offset, limit=validated_page_size)

    @staticmethod
    def delete_case(db: Session, case_id: int) -> Case:
        case = CaseRepository.get(db, case_id=case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        return CaseRepository.delete(db, case_id=case_id)

    @staticmethod
    def compare_cases(db: Session, case_id_a: int, case_id_b: int) -> dict:
        from app.models.cdr_record import CDRRecord
        from app.models.measurement import Measurement
        from app.models.movement_event import MovementEvent
        from scientific.pipeline.case_comparison import compare_cases as sc_compare_cases
        from dataclasses import asdict

        case_a = CaseRepository.get(db, case_id=case_id_a)
        if not case_a:
            raise HTTPException(status_code=404, detail=f"Case {case_id_a} not found")

        case_b = CaseRepository.get(db, case_id=case_id_b)
        if not case_b:
            raise HTTPException(status_code=404, detail=f"Case {case_id_b} not found")

        records_a = db.query(CDRRecord).filter(CDRRecord.case_id == case_id_a).all()
        if not records_a:
            records_a = db.query(Measurement).filter(Measurement.case_id == case_id_a).all()

        records_b = db.query(CDRRecord).filter(CDRRecord.case_id == case_id_b).all()
        if not records_b:
            records_b = db.query(Measurement).filter(Measurement.case_id == case_id_b).all()

        movements_a = db.query(MovementEvent).filter(MovementEvent.case_id == case_id_a).all()
        movements_b = db.query(MovementEvent).filter(MovementEvent.case_id == case_id_b).all()

        result = sc_compare_cases(
            case_a_records=records_a,
            case_b_records=records_b,
            case_a_movements=movements_a if movements_a else None,
            case_b_movements=movements_b if movements_b else None,
            case_a_id=getattr(case_a, "reference_number", None) or f"CASE-{case_id_a:03d}",
            case_b_id=getattr(case_b, "reference_number", None) or f"CASE-{case_id_b:03d}",
        )

        return asdict(result)

