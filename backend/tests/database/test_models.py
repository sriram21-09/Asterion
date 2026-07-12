import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base
from app.models.case import Case
from app.models.scenario import Scenario


@pytest.fixture(scope="function")
def db_session():
    """Create a temporary in-memory database and session for isolated testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def test_case_model_creation(db_session):
    """Test that we can create, insert, and retrieve a Case model."""
    new_case = Case(
        title="Test Investigation Case",
        description="A case description for unit testing.",
        status="active",
    )
    db_session.add(new_case)
    db_session.commit()

    # Retrieve the case
    retrieved_case = (
        db_session.query(Case).filter_by(title="Test Investigation Case").first()
    )
    assert retrieved_case is not None
    assert retrieved_case.id is not None
    assert retrieved_case.description == "A case description for unit testing."
    assert retrieved_case.status == "active"
    assert isinstance(retrieved_case.created_at, datetime)
    assert isinstance(retrieved_case.updated_at, datetime)


def test_scenario_model_creation(db_session):
    """Test that we can create, insert, and retrieve a Scenario model."""
    new_scenario = Scenario(
        name="Test Urban Scenario",
        description="An urban environment scenario configuration.",
    )
    db_session.add(new_scenario)
    db_session.commit()

    # Retrieve the scenario
    retrieved_scenario = (
        db_session.query(Scenario).filter_by(name="Test Urban Scenario").first()
    )
    assert retrieved_scenario is not None
    assert retrieved_scenario.id is not None
    assert (
        retrieved_scenario.description == "An urban environment scenario configuration."
    )
    assert isinstance(retrieved_scenario.created_at, datetime)
    assert isinstance(retrieved_scenario.updated_at, datetime)
