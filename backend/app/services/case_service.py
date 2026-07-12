from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.repositories.case_repository import CaseRepository
from app.repositories.scenario_repository import ScenarioRepository
from app.schemas.case import CaseCreate
from app.models.case import Case
from app.shared.validation import (
    validate_non_empty_string,
    validate_pagination,
    pagination_offset,
    ValidationError,
)
from typing import List, Optional


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
        db: Session, page: Optional[int] = None, page_size: Optional[int] = None
    ) -> List[Case]:
        validated_page, validated_page_size = validate_pagination(page, page_size)
        offset = pagination_offset(validated_page, validated_page_size)
        return CaseRepository.get_multi(db, skip=offset, limit=validated_page_size)

    @staticmethod
    def delete_case(db: Session, case_id: int) -> Case:
        case = CaseRepository.get(db, case_id=case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        return CaseRepository.delete(db, case_id=case_id)
