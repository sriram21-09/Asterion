"""
Database Model Tests — Cases & Scenarios
==========================================

Tests for the Cases and Scenarios ORM models using an in-memory SQLite
database. These tests validate table creation, field constraints, and
auto-populated timestamps.

Note:
    These tests use inline ORM model definitions that mirror the expected
    schema from the Week 1 Master Plan. Once Sriram's backend models are
    merged (backend/app/models/), the imports should be updated to:

        from backend.app.models.case import Case
        from backend.app.models.scenario import Scenario

    The inline definitions below can then be removed.
"""

from datetime import datetime, timezone
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

# Setup path for backend imports
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.models.base import Base
from app.models.case import Case
from app.models.scenario import Scenario
from app.models.tower import Tower

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh in-memory SQLite database and session for each test.

    Yields:
        Session: A SQLAlchemy session bound to an in-memory database.
    """
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


# ---------------------------------------------------------------------------
# Case Model Tests
# ---------------------------------------------------------------------------


class TestCaseModel:
    """Tests for the Cases ORM model."""

    def test_create_case_valid(self, db_session: Session):
        """Create a Case with title and description — verify all fields."""
        case = Case(
            title="Missing Person Investigation",
            description="Localization of last known device signals.",
        )
        db_session.add(case)
        db_session.commit()
        db_session.refresh(case)

        assert case.id is not None
        assert case.id > 0
        assert case.title == "Missing Person Investigation"
        assert case.description == "Localization of last known device signals."
        assert case.status == "open"
        assert case.created_at is not None
        assert case.updated_at is not None

    def test_create_case_missing_title_fails(self, db_session: Session):
        """Attempt to create a Case without a required title — expect failure."""
        case = Case(title=None, description="No title provided.")
        db_session.add(case)

        with pytest.raises(IntegrityError):
            db_session.commit()

        db_session.rollback()

    def test_case_timestamps_auto_set(self, db_session: Session):
        """Verify that created_at and updated_at are automatically populated."""
        datetime.now(timezone.utc)

        case = Case(title="Timestamp Test Case")
        db_session.add(case)
        db_session.commit()
        db_session.refresh(case)

        datetime.now(timezone.utc)

        # created_at should be between before and after
        assert case.created_at is not None
        assert isinstance(case.created_at, datetime)

        # updated_at should also be auto-set
        assert case.updated_at is not None
        assert isinstance(case.updated_at, datetime)

    def test_case_default_status_is_open(self, db_session: Session):
        """Verify that the default status is 'open'."""
        case = Case(title="Default Status Test")
        db_session.add(case)
        db_session.commit()
        db_session.refresh(case)

        assert case.status == "open"


# ---------------------------------------------------------------------------
# Scenario Model Tests
# ---------------------------------------------------------------------------


class TestScenarioModel:
    """Tests for the Scenarios ORM model."""

    def test_create_scenario_valid(self, db_session: Session):
        """Create a Scenario with name and description — verify persistence."""
        scenario = Scenario(
            name="Urban 3-Tower Test",
            description="Basic multilateration scenario with 3 towers.",
        )
        db_session.add(scenario)
        db_session.commit()
        db_session.refresh(scenario)

        assert scenario.id is not None
        assert scenario.id > 0
        assert scenario.name == "Urban 3-Tower Test"
        assert scenario.description == "Basic multilateration scenario with 3 towers."
        assert scenario.created_at is not None

    def test_create_scenario_missing_name_fails(self, db_session: Session):
        """Attempt to create a Scenario without a name — expect failure."""
        scenario = Scenario(name=None, description="No name provided.")
        db_session.add(scenario)

        with pytest.raises(IntegrityError):
            db_session.commit()

        db_session.rollback()

    def test_create_scenario_without_description(self, db_session: Session):
        """Create a Scenario without a description — should succeed."""
        scenario = Scenario(name="Minimal Scenario")
        db_session.add(scenario)
        db_session.commit()
        db_session.refresh(scenario)

        assert scenario.id is not None
        assert scenario.name == "Minimal Scenario"
        assert scenario.description is None

    def test_scenario_created_at_auto_set(self, db_session: Session):
        """Verify that created_at is automatically populated."""
        scenario = Scenario(name="Timestamp Test Scenario")
        db_session.add(scenario)
        db_session.commit()
        db_session.refresh(scenario)

        assert scenario.created_at is not None
        assert isinstance(scenario.created_at, datetime)


class TestRelationshipCaseScenario:
    """Tests for the relationship and foreign keys between Case and Scenario."""

    def test_case_scenario_relationship(self, db_session: Session):
        """Verify that a Case can be associated with a Scenario."""
        scenario = Scenario(name="Scenario A", description="Test Scenario A")
        db_session.add(scenario)
        db_session.commit()
        db_session.refresh(scenario)

        case = Case(title="Case A", scenario_id=scenario.id)
        db_session.add(case)
        db_session.commit()
        db_session.refresh(case)

        # Verify foreign key constraint & relations
        assert case.scenario_id == scenario.id
        assert case.scenario is not None
        assert case.scenario.name == "Scenario A"
        assert len(scenario.cases) == 1
        assert scenario.cases[0].title == "Case A"

    def test_delete_scenario_nullifies_case_foreign_key(self, db_session: Session):
        """Verify that deleting a Scenario sets the scenario_id on Case to NULL (SET NULL behavior)."""
        scenario = Scenario(name="Scenario B")
        db_session.add(scenario)
        db_session.commit()
        db_session.refresh(scenario)

        case = Case(title="Case B", scenario_id=scenario.id)
        db_session.add(case)
        db_session.commit()
        db_session.refresh(case)

        # Delete scenario
        db_session.delete(scenario)
        db_session.commit()
        db_session.refresh(case)

        # scenario_id should be NULL now
        assert case.scenario_id is None
        assert case.scenario is None


class TestTowerModel:
    """Tests for the Towers ORM model."""

    def test_create_tower_valid(self, db_session: Session):
        """Create a Tower with name, lat, lon, and sector — verify persistence."""
        tower = Tower(
            tower_name="Tower Alpha",
            latitude=12.9716,
            longitude=77.5946,
            sector="A",
        )
        db_session.add(tower)
        db_session.commit()
        db_session.refresh(tower)

        assert tower.id is not None
        assert tower.id > 0
        assert tower.tower_name == "Tower Alpha"
        assert tower.latitude == 12.9716
        assert tower.longitude == 77.5946
        assert tower.sector == "A"
        assert tower.created_at is not None
        assert tower.updated_at is not None

    def test_create_tower_missing_name_fails(self, db_session: Session):
        """Attempt to create a Tower without a name — expect failure."""
        tower = Tower(tower_name=None, latitude=12.9716, longitude=77.5946)
        db_session.add(tower)

        with pytest.raises(IntegrityError):
            db_session.commit()

        db_session.rollback()
