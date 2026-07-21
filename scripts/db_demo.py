"""
Asterion Database Validation Demo Script
========================================

This script demonstrates and validates the database constraints, relationships,
and model properties for Cases, Scenarios, and Towers during the Week 1 Sprint Review.

Usage:
    python scripts/db_demo.py
"""

import sys
from pathlib import Path

# Setup path for backend imports
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.models.case import Case
from app.models.scenario import Scenario
from app.models.tower import Tower


def run_demo():
    print("=" * 60)
    print("      ASTERION DATABASE VALIDATION DEMO - SPRINT REVIEW      ")
    print("=" * 60)

    # 1. Initialize fresh in-memory SQLite database
    print("\n[Step 1] Initializing in-memory SQLite database...")
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    print("[OK] Database tables created successfully.")

    # 2. Insert valid models
    print("\n[Step 2] Inserting valid database records...")

    # Create a scenario
    scenario = Scenario(
        name="Urban 3-Tower Test",
        description="Standard multilateration scenario in Bangalore core.",
    )
    session.add(scenario)
    session.commit()
    print(f"[OK] Scenario created: '{scenario.name}' (ID: {scenario.id})")

    # Create a case associated with the scenario
    case = Case(
        title="Missing Person Investigation #41",
        description="Locating device signals last seen near MG Road.",
        scenario_id=scenario.id,
    )
    session.add(case)
    session.commit()
    print(
        f"[OK] Case created: '{case.title}' (ID: {case.id}, Scenario ID: {case.scenario_id})"
    )

    # Create cell towers
    towers = [
        Tower(
            tower_name="Tower Alpha", latitude=12.9716, longitude=77.5946, sector="A"
        ),
        Tower(tower_name="Tower Beta", latitude=12.9753, longitude=77.5910, sector="B"),
        Tower(
            tower_name="Tower Gamma", latitude=12.9680, longitude=77.5992, sector="C"
        ),
    ]
    session.add_all(towers)
    session.commit()
    print("[OK] Towers created:")
    for t in towers:
        print(f"   - {t.tower_name} (ID: {t.id}, Coords: {t.latitude}, {t.longitude})")

    # 3. Validate database constraints (IntegrityError)
    print("\n[Step 3] Validating database integrity constraints...")

    # Try inserting case without a title
    invalid_case = Case(title=None, description="This should fail.")
    session.add(invalid_case)
    try:
        session.commit()
        print("[FAIL] ERROR: Case without title was saved (Constraint bypass).")
    except IntegrityError:
        session.rollback()
        print("[OK] SUCCESS: Case without title was blocked by database constraints.")

    # Try inserting tower without a name
    invalid_tower = Tower(tower_name=None, latitude=12.9716, longitude=77.5946)
    session.add(invalid_tower)
    try:
        session.commit()
        print("[FAIL] ERROR: Tower without name was saved (Constraint bypass).")
    except IntegrityError:
        session.rollback()
        print("[OK] SUCCESS: Tower without name was blocked by database constraints.")

    # 4. Validate cascade/SET NULL relationships
    print("\n[Step 4] Validating relationships (SET NULL on delete)...")
    print(f"Before Scenario deletion: Case scenario_id = {case.scenario_id}")

    # Delete the scenario
    session.delete(scenario)
    session.commit()
    session.refresh(case)

    print(f"After Scenario deletion: Case scenario_id = {case.scenario_id}")
    if case.scenario_id is None:
        print(
            "[OK] SUCCESS: Deleting a Scenario set Case scenario_id to NULL (as configured)."
        )
    else:
        print("[FAIL] ERROR: Deleting a Scenario failed to nullify Case scenario_id.")

    # 5. Clean up
    session.close()
    engine.dispose()
    print("\n" + "=" * 60)
    print("                  DEMO COMPLETED SUCCESSFULLY                 ")
    print("=" * 60)


if __name__ == "__main__":
    run_demo()
