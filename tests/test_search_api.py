"""Comprehensive test suite for the Global Search API (Issue #134).

Tests cover:
- Search by IMEI, IMSI, MSISDN, Cell ID, Tower CGI, Tower CI, Case title
- Partial match support
- Cross-type search results
- Pagination (limit/offset)
- Empty query validation (HTTP 400)
- SQL injection safety
- Response schema with type discriminator
"""

import pytest
from app.database.base import Base
from app.database.session import get_db
from app.models.case import Case
from app.models.cdr_record import CDRRecord
from app.models.import_job import ImportJob
from app.models.tower import Tower
from fastapi.testclient import TestClient
from main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database session for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session: Session):
    """Create a test client with the database session override."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def seed_data(db_session: Session):
    """Seed the database with test data across CDR records, towers, and cases."""
    # Create an import job (required FK for CDR records)
    import_job = ImportJob(
        filename="test_search.csv",
        operator="airtel",
        status="completed",
        total_records=3,
        parsed_records=3,
        failed_records=0,
    )
    db_session.add(import_job)
    db_session.flush()

    # Create CDR records with various searchable fields
    cdr1 = CDRRecord(
        import_job_id=import_job.id,
        operator="airtel",
        target_number="9876543210",
        imei="356938035643809",
        imsi="404980123456789",
        first_cgi="404-98-8331-23071",
        last_cgi="404-98-8331-23072",
        call_type="MOC",
    )
    cdr2 = CDRRecord(
        import_job_id=import_job.id,
        operator="bsnl",
        target_number="9123456780",
        imei="867322041528374",
        imsi="404810987654321",
        first_cgi="404-81-724-24723",
        call_type="MTC",
    )
    cdr3 = CDRRecord(
        import_job_id=import_job.id,
        operator="jio",
        target_number="7890123456",
        imei="490154203237518",
        imsi="405874567890123",
        first_cgi="405-87-1001-50001",
        call_type="SMS",
    )
    db_session.add_all([cdr1, cdr2, cdr3])

    # Create towers
    tower1 = Tower(
        tower_name="Tower Alpha",
        cgi="404-98-8331-23071",
        mcc="404",
        mnc="98",
        lac="8331",
        ci="23071",
        operator="Airtel",
        latitude=21.29669,
        longitude=72.8915,
    )
    tower2 = Tower(
        tower_name="Tower Beta",
        cgi="404-81-724-24723",
        mcc="404",
        mnc="81",
        lac="724",
        ci="24723",
        operator="BSNL",
        latitude=22.39711,
        longitude=88.43938,
    )
    db_session.add_all([tower1, tower2])

    # Create cases
    case1 = Case(
        title="Investigation IMEI Tracking",
        description="Tracking suspect device with IMEI 356938035643809",
        status="open",
    )
    case2 = Case(
        title="Mumbai Tower Analysis",
        description="Coverage analysis for towers in the Mumbai region",
        status="closed",
    )
    db_session.add_all([case1, case2])
    db_session.commit()

    return {
        "import_job": import_job,
        "cdr_records": [cdr1, cdr2, cdr3],
        "towers": [tower1, tower2],
        "cases": [case1, case2],
    }


# ============================================================================
# Unit Tests: Search by Individual Fields
# ============================================================================


class TestSearchByIMEI:
    """Test searching by IMEI number."""

    def test_exact_imei_match(self, client, seed_data):
        resp = client.get("/api/v1/search", params={"q": "356938035643809"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        results = data["data"]["results"]
        # Should match CDR record with this IMEI
        cdr_results = [r for r in results if r["result_type"] == "cdr_record"]
        assert len(cdr_results) >= 1
        assert any(r["imei"] == "356938035643809" for r in cdr_results)

    def test_partial_imei_match(self, client, seed_data):
        resp = client.get("/api/v1/search", params={"q": "356938"})
        assert resp.status_code == 200
        data = resp.json()
        results = data["data"]["results"]
        cdr_results = [r for r in results if r["result_type"] == "cdr_record"]
        assert len(cdr_results) >= 1


class TestSearchByIMSI:
    """Test searching by IMSI number."""

    def test_exact_imsi_match(self, client, seed_data):
        resp = client.get("/api/v1/search", params={"q": "404980123456789"})
        assert resp.status_code == 200
        data = resp.json()
        results = data["data"]["results"]
        cdr_results = [r for r in results if r["result_type"] == "cdr_record"]
        assert len(cdr_results) >= 1
        assert any(r["imsi"] == "404980123456789" for r in cdr_results)


class TestSearchByMSISDN:
    """Test searching by MSISDN (target_number)."""

    def test_exact_msisdn_match(self, client, seed_data):
        resp = client.get("/api/v1/search", params={"q": "9876543210"})
        assert resp.status_code == 200
        data = resp.json()
        results = data["data"]["results"]
        cdr_results = [r for r in results if r["result_type"] == "cdr_record"]
        assert len(cdr_results) >= 1
        assert any(r["target_number"] == "9876543210" for r in cdr_results)

    def test_partial_msisdn_match(self, client, seed_data):
        resp = client.get("/api/v1/search", params={"q": "987654"})
        assert resp.status_code == 200
        data = resp.json()
        results = data["data"]["results"]
        assert len(results) >= 1


class TestSearchByCellID:
    """Test searching by Cell ID (first_cgi / last_cgi)."""

    def test_search_by_first_cgi(self, client, seed_data):
        resp = client.get("/api/v1/search", params={"q": "404-98-8331-23071"})
        assert resp.status_code == 200
        data = resp.json()
        results = data["data"]["results"]
        # Should match both CDR record (first_cgi) and Tower (cgi)
        cdr_results = [r for r in results if r["result_type"] == "cdr_record"]
        tower_results = [r for r in results if r["result_type"] == "tower"]
        assert len(cdr_results) >= 1
        assert len(tower_results) >= 1

    def test_search_by_last_cgi(self, client, seed_data):
        resp = client.get("/api/v1/search", params={"q": "404-98-8331-23072"})
        assert resp.status_code == 200
        data = resp.json()
        results = data["data"]["results"]
        cdr_results = [r for r in results if r["result_type"] == "cdr_record"]
        assert len(cdr_results) >= 1


class TestSearchByTower:
    """Test searching by Tower CGI and CI."""

    def test_search_by_tower_cgi(self, client, seed_data):
        resp = client.get("/api/v1/search", params={"q": "404-81-724-24723"})
        assert resp.status_code == 200
        data = resp.json()
        results = data["data"]["results"]
        tower_results = [r for r in results if r["result_type"] == "tower"]
        assert len(tower_results) >= 1
        assert any(r["cgi"] == "404-81-724-24723" for r in tower_results)

    def test_search_by_tower_ci(self, client, seed_data):
        resp = client.get("/api/v1/search", params={"q": "23071"})
        assert resp.status_code == 200
        data = resp.json()
        results = data["data"]["results"]
        tower_results = [r for r in results if r["result_type"] == "tower"]
        assert len(tower_results) >= 1
        assert any(r["ci"] == "23071" for r in tower_results)


class TestSearchByCase:
    """Test searching by Case title and description."""

    def test_search_by_case_title(self, client, seed_data):
        resp = client.get("/api/v1/search", params={"q": "Investigation"})
        assert resp.status_code == 200
        data = resp.json()
        results = data["data"]["results"]
        case_results = [r for r in results if r["result_type"] == "case"]
        assert len(case_results) >= 1
        assert any("Investigation" in r["title"] for r in case_results)

    def test_search_by_case_description(self, client, seed_data):
        resp = client.get("/api/v1/search", params={"q": "Mumbai"})
        assert resp.status_code == 200
        data = resp.json()
        results = data["data"]["results"]
        case_results = [r for r in results if r["result_type"] == "case"]
        assert len(case_results) >= 1


# ============================================================================
# Cross-Type Search Tests
# ============================================================================


class TestCrossTypeSearch:
    """Test searches that match across multiple entity types."""

    def test_query_matching_cdr_and_tower(self, client, seed_data):
        # "404-98-8331-23071" matches CDR first_cgi and Tower cgi
        resp = client.get("/api/v1/search", params={"q": "404-98-8331-23071"})
        assert resp.status_code == 200
        data = resp.json()
        results = data["data"]["results"]
        result_types = {r["result_type"] for r in results}
        assert "cdr_record" in result_types
        assert "tower" in result_types

    def test_query_matching_all_types(self, client, seed_data):
        # "IMEI" appears in case title, and partial IMEI digits may match CDR
        resp = client.get("/api/v1/search", params={"q": "IMEI"})
        assert resp.status_code == 200
        data = resp.json()
        results = data["data"]["results"]
        case_results = [r for r in results if r["result_type"] == "case"]
        assert len(case_results) >= 1

    def test_no_results_found(self, client, seed_data):
        resp = client.get("/api/v1/search", params={"q": "zzz_nonexistent_term_zzz"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["total"] == 0
        assert data["data"]["results"] == []


# ============================================================================
# Pagination Tests
# ============================================================================


class TestPagination:
    """Test pagination support with limit/offset parameters."""

    def test_default_pagination(self, client, seed_data):
        resp = client.get("/api/v1/search", params={"q": "404"})
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["limit"] == 20
        assert data["offset"] == 0
        assert data["total"] >= 1

    def test_custom_limit(self, client, seed_data):
        resp = client.get("/api/v1/search", params={"q": "404", "limit": 2})
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["limit"] == 2
        assert len(data["results"]) <= 2

    def test_offset_skips_results(self, client, seed_data):
        # Get total first
        resp_all = client.get("/api/v1/search", params={"q": "404", "limit": 100})
        total = resp_all.json()["data"]["total"]

        if total > 1:
            # Offset by 1, should skip the first result
            resp_offset = client.get(
                "/api/v1/search", params={"q": "404", "limit": 100, "offset": 1}
            )
            offset_results = resp_offset.json()["data"]["results"]
            assert len(offset_results) == total - 1
            # The total should remain the same
            assert resp_offset.json()["data"]["total"] == total

    def test_offset_beyond_results(self, client, seed_data):
        resp = client.get("/api/v1/search", params={"q": "404", "offset": 1000})
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["results"] == []
        assert data["total"] >= 1  # total count is unaffected by offset

    def test_limit_one_returns_single_result(self, client, seed_data):
        resp = client.get("/api/v1/search", params={"q": "404", "limit": 1})
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data["results"]) <= 1


# ============================================================================
# Validation Tests
# ============================================================================


class TestQueryValidation:
    """Test query parameter validation and error handling."""

    def test_missing_query_returns_422(self, client, seed_data):
        # FastAPI returns 422 for missing required query param
        resp = client.get("/api/v1/search")
        assert resp.status_code == 422

    def test_empty_query_returns_422(self, client, seed_data):
        # min_length=1 validation triggers 422
        resp = client.get("/api/v1/search", params={"q": ""})
        assert resp.status_code == 422

    def test_whitespace_only_query_returns_400(self, client, seed_data):
        # Passes min_length=1 but strip() makes it empty → HTTP 400
        resp = client.get("/api/v1/search", params={"q": "   "})
        assert resp.status_code == 400

    def test_invalid_limit_returns_422(self, client, seed_data):
        resp = client.get("/api/v1/search", params={"q": "test", "limit": 0})
        assert resp.status_code == 422

    def test_invalid_offset_returns_422(self, client, seed_data):
        resp = client.get("/api/v1/search", params={"q": "test", "offset": -1})
        assert resp.status_code == 422

    def test_limit_exceeds_max_returns_422(self, client, seed_data):
        resp = client.get("/api/v1/search", params={"q": "test", "limit": 101})
        assert resp.status_code == 422


# ============================================================================
# SQL Injection Safety Tests
# ============================================================================


class TestSQLInjectionSafety:
    """Test that SQL injection attempts are safely handled."""

    def test_sql_injection_drop_table(self, client, seed_data):
        resp = client.get(
            "/api/v1/search",
            params={"q": "'; DROP TABLE cdr_records;--"},
        )
        # Should return safely — either empty results or matched text
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_sql_injection_union_select(self, client, seed_data):
        resp = client.get(
            "/api/v1/search",
            params={"q": "' UNION SELECT * FROM cases --"},
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_sql_injection_or_true(self, client, seed_data):
        resp = client.get(
            "/api/v1/search",
            params={"q": "' OR '1'='1"},
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True


# ============================================================================
# Response Schema Tests
# ============================================================================


class TestResponseSchema:
    """Test response structure and type discriminator correctness."""

    def test_cdr_result_has_correct_type(self, client, seed_data):
        resp = client.get("/api/v1/search", params={"q": "356938035643809"})
        assert resp.status_code == 200
        results = resp.json()["data"]["results"]
        cdr_results = [r for r in results if r["result_type"] == "cdr_record"]
        for r in cdr_results:
            assert "id" in r
            assert "operator" in r
            assert "result_type" in r
            assert r["result_type"] == "cdr_record"

    def test_tower_result_has_correct_type(self, client, seed_data):
        resp = client.get("/api/v1/search", params={"q": "Tower Alpha"})
        assert resp.status_code == 200
        results = resp.json()["data"]["results"]
        tower_results = [r for r in results if r["result_type"] == "tower"]
        for r in tower_results:
            assert "id" in r
            assert "tower_name" in r
            assert r["result_type"] == "tower"

    def test_case_result_has_correct_type(self, client, seed_data):
        resp = client.get("/api/v1/search", params={"q": "Investigation"})
        assert resp.status_code == 200
        results = resp.json()["data"]["results"]
        case_results = [r for r in results if r["result_type"] == "case"]
        for r in case_results:
            assert "id" in r
            assert "title" in r
            assert "status" in r
            assert r["result_type"] == "case"

    def test_response_contains_pagination_metadata(self, client, seed_data):
        resp = client.get(
            "/api/v1/search", params={"q": "404", "limit": 5, "offset": 1}
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "results" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert "query" in data
        assert data["limit"] == 5
        assert data["offset"] == 1
        assert data["query"] == "404"
