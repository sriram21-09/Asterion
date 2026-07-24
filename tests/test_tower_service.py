"""Unit Tests for Tower Intelligence Service & CGI Lookups
=========================================================

Verifies database-backed CGI resolution, prefix fallback hierarchy, confidence score classification
(Known 1.0, Estimated 0.6, Unknown 0.2), Jio/Vi null coordinate handling, and API endpoints.
"""

import pytest
<<<<<<< HEAD
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from app.models.base import Base
from app.schemas.tower import TowerCreate
from app.services.tower_service import TowerIntelligenceService
from main import app
from app.database.session import get_db
=======
from app.database.session import get_db
from app.models.base import Base
from app.schemas.tower import TowerCreate
from app.services.tower_service import TowerIntelligenceService
from fastapi.testclient import TestClient
from main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
>>>>>>> 563df9fcb5b395c6734dc2284f99456f989bf468

# Configure in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    connection = engine.connect()
    Base.metadata.create_all(bind=connection)
    session = TestingSessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=connection)
        connection.close()


@pytest.fixture
def client(db_session):
    def _get_test_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _get_test_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


class TestConfidenceClassification:
    def test_classify_known_confidence(self):
        conf, cat = TowerIntelligenceService.classify_confidence(
            12.9716, 77.5946, "exact"
        )
        assert conf == 1.0
        assert cat == "Known"

    def test_classify_estimated_confidence(self):
        for method in ["prefix_lac", "prefix_mnc", "prefix_mcc", "estimated"]:
            conf, cat = TowerIntelligenceService.classify_confidence(
                12.9716, 77.5946, method
            )
            assert conf == 0.6
            assert cat == "Estimated"

    def test_classify_unknown_confidence(self):
        conf, cat = TowerIntelligenceService.classify_confidence(
            None, None, "unresolved"
        )
        assert conf == 0.2
        assert cat == "Unknown"

        # Even with method exact, if coordinates are None, it must be Unknown (0.2)
        conf2, cat2 = TowerIntelligenceService.classify_confidence(None, None, "exact")
        assert conf2 == 0.2
        assert cat2 == "Unknown"


class TestTowerRegistration:
    def test_register_tower_known_coordinates(self, db_session: Session):
        data = TowerCreate(
            tower_name="Airtel MG Road",
            cgi="404-98-8331-23071",
            operator="Airtel",
            latitude=12.9716,
            longitude=77.5946,
        )
        tower = TowerIntelligenceService.register_tower(db_session, data)
        assert tower.id is not None
        assert tower.latitude == 12.9716
        assert tower.longitude == 77.5946
        assert tower.confidence == 1.0
        assert tower.confidence_category == "Known"
        assert tower.mcc == "404"
        assert tower.mnc == "98"

    def test_register_jio_vi_tower_missing_coordinates(self, db_session: Session):
        """CRITICAL: Jio and Vi towers without coordinates must be recorded as null with 0.2 confidence. Do NOT default to (0,0)."""
        data_jio = TowerCreate(
            tower_name="Jio Indiranagar",
            cgi="405-86-5000-1234",
            operator="Jio",
            latitude=None,
            longitude=None,
        )
        tower = TowerIntelligenceService.register_tower(db_session, data_jio)
        assert tower.id is not None
        assert tower.latitude is None
        assert tower.longitude is None
        assert tower.latitude != 0.0
        assert tower.longitude != 0.0
        assert tower.confidence == 0.2
        assert tower.confidence_category == "Unknown"

    def test_register_vi_tower_empty_coordinates(self, db_session: Session):
        data_vi = TowerCreate(
            tower_name="Vi Koramangala",
            cgi="404-20-6000-5678",
            operator="Vi",
            latitude=None,
            longitude=None,
        )
        tower = TowerIntelligenceService.register_tower(db_session, data_vi)
        assert tower.latitude is None
        assert tower.longitude is None
        assert tower.confidence == 0.2
        assert tower.confidence_category == "Unknown"


class TestCGILookupFallback:
    @pytest.fixture
    def populated_db(self, db_session: Session):
        # 1. Exact Tower
        TowerIntelligenceService.register_tower(
            db_session,
            TowerCreate(
                tower_name="T_EXACT",
                cgi="404-98-1000-1",
                operator="Airtel",
                latitude=10.0,
                longitude=20.0,
            ),
        )
        # 2. Towers in same LAC (mcc=404, mnc=45, lac=2000)
        TowerIntelligenceService.register_tower(
            db_session,
            TowerCreate(
                tower_name="T_LAC_1",
                cgi="404-45-2000-10",
                operator="BSNL",
                latitude=12.0,
                longitude=30.0,
            ),
        )
        TowerIntelligenceService.register_tower(
            db_session,
            TowerCreate(
                tower_name="T_LAC_2",
                cgi="404-45-2000-11",
                operator="BSNL",
                latitude=14.0,
                longitude=32.0,
            ),
        )
        # 3. Jio Tower without coordinates in LAC 2000 (should be ignored in centroid average)
        TowerIntelligenceService.register_tower(
            db_session,
            TowerCreate(
                tower_name="T_LAC_JIO_NULL",
                cgi="404-45-2000-12",
                operator="Jio",
                latitude=None,
                longitude=None,
            ),
        )
        # 4. Towers in same MNC (mcc=404, mnc=50)
        TowerIntelligenceService.register_tower(
            db_session,
            TowerCreate(
                tower_name="T_MNC_1",
                cgi="404-50-3000-100",
                operator="Airtel",
                latitude=15.0,
                longitude=40.0,
            ),
        )
        # 5. Towers in same MCC (mcc=405)
        TowerIntelligenceService.register_tower(
            db_session,
            TowerCreate(
                tower_name="T_MCC_1",
                cgi="405-99-4000-999",
                operator="Vi",
                latitude=25.0,
                longitude=50.0,
            ),
        )
        return db_session

    def test_resolve_exact_match(self, populated_db: Session):
        res = TowerIntelligenceService.resolve_cgi(populated_db, "404-98-1000-1")
        assert res.resolved_latitude == 10.0
        assert res.resolved_longitude == 20.0
        assert res.confidence == 1.0
        assert res.confidence_category == "Known"
        assert res.resolution_method == "exact"
        assert res.matched_towers_count == 1

    def test_resolve_lac_prefix_fallback(self, populated_db: Session):
        # CI 999 doesn't exist, should fall back to centroid of LAC 2000 (average of (12, 30) and (14, 32))
        res = TowerIntelligenceService.resolve_cgi(populated_db, "404-45-2000-999")
        assert res.resolved_latitude == 13.0
        assert res.resolved_longitude == 31.0
        assert res.confidence == 0.6
        assert res.confidence_category == "Estimated"
        assert res.resolution_method == "prefix_lac"
        assert (
            res.matched_towers_count == 2
        )  # The null tower is ignored in centroid count

    def test_resolve_mnc_prefix_fallback(self, populated_db: Session):
        # LAC 9999 and CI 9999 don't exist -> MNC 50 fallback
        res = TowerIntelligenceService.resolve_cgi(populated_db, "404-50-9999-9999")
        assert res.resolved_latitude == 15.0
        assert res.resolved_longitude == 40.0
        assert res.confidence == 0.6
        assert res.confidence_category == "Estimated"
        assert res.resolution_method == "prefix_mnc"

    def test_resolve_mcc_prefix_fallback(self, populated_db: Session):
        # MNC 88 doesn't exist -> MCC 405 fallback
        res = TowerIntelligenceService.resolve_cgi(populated_db, "405-88-9999-9999")
        assert res.resolved_latitude == 25.0
        assert res.resolved_longitude == 50.0
        assert res.confidence == 0.6
        assert res.confidence_category == "Estimated"
        assert res.resolution_method == "prefix_mcc"

    def test_resolve_unresolved(self, populated_db: Session):
        res = TowerIntelligenceService.resolve_cgi(populated_db, "999-99-9999-9999")
        assert res.resolved_latitude is None
        assert res.resolved_longitude is None
        assert res.confidence == 0.2
        assert res.confidence_category == "Unknown"
        assert res.resolution_method == "unresolved"
        assert res.matched_towers_count == 0


class TestBulkCDRRecordResolution:
    def test_bulk_resolve_cdr_records(self, db_session: Session):
        TowerIntelligenceService.register_tower(
            db_session,
            TowerCreate(
                tower_name="Tower 1",
                cgi="404-98-100-1",
                latitude=12.5,
                longitude=77.5,
            ),
        )

        records = [
            {"cgi": "404-98-100-1", "latitude": None, "longitude": None},
            {
                "cgi": "404-98-100-99",
                "latitude": None,
                "longitude": None,
            },  # LAC fallback
            {"cgi": "999-99-999-9", "latitude": None, "longitude": None},  # Unresolved
        ]

        resolved = TowerIntelligenceService.bulk_resolve_cdr_records(
            db_session, records
        )
        assert resolved[0]["latitude"] == 12.5
        assert resolved[0]["tower_confidence"] == 1.0
        assert resolved[0]["tower_confidence_category"] == "Known"

        assert resolved[1]["latitude"] == 12.5  # LAC fallback
        assert resolved[1]["tower_confidence"] == 0.6
        assert resolved[1]["tower_confidence_category"] == "Estimated"

        assert resolved[2]["latitude"] is None  # Unresolved
        assert resolved[2]["tower_confidence"] == 0.2
        assert resolved[2]["tower_confidence_category"] == "Unknown"


class TestTowerAPIEndpoints:
    def test_api_register_and_list_towers(self, client: TestClient):
        response = client.post(
            "/api/v1/towers",
            json={
                "tower_name": "API Tower 1",
                "cgi": "404-98-8888-1",
                "operator": "Airtel",
                "latitude": 13.0,
                "longitude": 77.6,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["confidence"] == 1.0
        assert data["data"]["confidence_category"] == "Known"

        # List towers
        list_resp = client.get("/api/v1/towers")
        assert list_resp.status_code == 200
        list_data = list_resp.json()
        assert len(list_data["data"]) == 1

    def test_api_cgi_lookup(self, client: TestClient):
        client.post(
            "/api/v1/towers",
            json={
                "tower_name": "API Tower Exact",
                "cgi": "404-98-7777-10",
                "operator": "BSNL",
                "latitude": 13.5,
                "longitude": 78.0,
            },
        )

        lookup_resp = client.post(
            "/api/v1/towers/lookup",
            json={"cgi": "404-98-7777-10"},
        )
        assert lookup_resp.status_code == 200
        data = lookup_resp.json()["data"]
        assert data["resolved_latitude"] == 13.5
        assert data["resolved_longitude"] == 78.0
        assert data["confidence"] == 1.0
        assert data["confidence_category"] == "Known"

    def test_api_jio_vi_null_lookup(self, client: TestClient):
        # Register Jio tower with null coordinates
        client.post(
            "/api/v1/towers",
            json={
                "tower_name": "Jio Tower Null",
                "cgi": "405-86-9000-1",
                "operator": "Jio",
                "latitude": None,
                "longitude": None,
            },
        )

        lookup_resp = client.post(
            "/api/v1/towers/lookup",
            json={"cgi": "405-86-9000-1"},
        )
        assert lookup_resp.status_code == 200
        data = lookup_resp.json()["data"]
        assert data["resolved_latitude"] is None
        assert data["resolved_longitude"] is None
        assert data["confidence"] == 0.2
        assert data["confidence_category"] == "Unknown"
