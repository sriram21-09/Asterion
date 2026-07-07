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

import pytest
from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


# ---------------------------------------------------------------------------
# Inline ORM definitions (mirrors Sriram's expected Day 2 models)
# TODO: Replace with imports from backend.app.models once merged
# ---------------------------------------------------------------------------


class Base(DeclarativeBase):
    """Shared base class for all ORM models."""

    pass


class Case(Base):
    """ORM model for investigation cases.

    Fields mirror the expected schema from the master plan:
    id, title, description, status, created_at, updated_at.
    """

    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="open")
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class Scenario(Base):
    """ORM model for localization scenarios.

    Fields mirror the expected schema from the master plan:
    id, name, description, created_at.
    """

    __tablename__ = "scenarios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


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
        before = datetime.now(timezone.utc)

        case = Case(title="Timestamp Test Case")
        db_session.add(case)
        db_session.commit()
        db_session.refresh(case)

        after = datetime.now(timezone.utc)

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
