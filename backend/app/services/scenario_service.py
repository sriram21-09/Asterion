from app.models.scenario import Scenario
from app.repositories.scenario_repository import ScenarioRepository
from app.schemas.scenario import ScenarioCreate
from app.shared.validation import (
    ValidationError,
    pagination_offset,
    validate_non_empty_string,
    validate_pagination,
)
from fastapi import HTTPException
from sqlalchemy.orm import Session


class ScenarioService:
    """Service class for Scenario business logic and validation.

    # ponytail: simple static class wrapper for business actions
    """

    @staticmethod
    def create_scenario(db: Session, scenario_in: ScenarioCreate) -> Scenario:
        # Validate name is non-empty and <= 255 chars
        name = validate_non_empty_string(scenario_in.name, "name", max_length=255)

        # Validate description length if provided
        description = None
        if scenario_in.description is not None:
            # Empty description can be treated as None, otherwise validate
            stripped = scenario_in.description.strip()
            if stripped:
                description = validate_non_empty_string(
                    stripped, "description", max_length=1000
                )

        # Check for unique name constraint
        existing = ScenarioRepository.get_by_name(db, name=name)
        if existing:
            raise ValidationError(
                "name", "Scenario with this name already exists.", status_code=400
            )

        return ScenarioRepository.create(db, name=name, description=description)

    @staticmethod
    def get_scenario(db: Session, scenario_id: int) -> Scenario:
        scenario = ScenarioRepository.get(db, scenario_id=scenario_id)
        if not scenario:
            raise HTTPException(status_code=404, detail="Scenario not found")
        return scenario

    @staticmethod
    def list_scenarios(
        db: Session, page: int | None = None, page_size: int | None = None
    ) -> list[Scenario]:
        validated_page, validated_page_size = validate_pagination(page, page_size)
        offset = pagination_offset(validated_page, validated_page_size)
        return ScenarioRepository.get_multi(db, skip=offset, limit=validated_page_size)

    @staticmethod
    def delete_scenario(db: Session, scenario_id: int) -> Scenario:
        scenario = ScenarioRepository.get(db, scenario_id=scenario_id)
        if not scenario:
            raise HTTPException(status_code=404, detail="Scenario not found")
        return ScenarioRepository.delete(db, scenario_id=scenario_id)
