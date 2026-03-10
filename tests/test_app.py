"""
Tests for the reverse phone search application.
"""
import pytest

from app import app as flask_app
from database import init_db, lookup_phone


@pytest.fixture()
def db_path(tmp_path):
    """Create a temporary SQLite database seeded with sample data."""
    path = str(tmp_path / "test.db")
    init_db(db_path=path)
    return path


@pytest.fixture()
def app(db_path, monkeypatch):
    """Configure Flask app to use the temporary test database."""
    monkeypatch.setenv("DB_PATH", db_path)
    flask_app.config["TESTING"] = True
    yield flask_app


@pytest.fixture()
def client(app):
    return app.test_client()


# ---------------------------------------------------------------------------
# database layer tests
# ---------------------------------------------------------------------------

class TestDatabase:
    def test_lookup_known_number_basic_fields(self, db_path):
        result = lookup_phone("+12025550101", db_path=db_path)
        assert result is not None
        assert result["name"] == "Alice Johnson"
        assert result["city"] == "Washington"
        assert result["state"] == "DC"

    def test_lookup_known_number_rich_fields(self, db_path):
        result = lookup_phone("+12025550101", db_path=db_path)
        assert result["age"] == 34
        assert result["line_type"] == "Cell"
        assert result["carrier"] == "AT&T"
        assert result["email"] == "alice.johnson@example.com"
        assert result["job_title"] == "Software Engineer"
        assert result["employer"] == "Tech Corp"

    def test_lookup_spam_number(self, db_path):
        result = lookup_phone("+18005551234", db_path=db_path)
        assert result is not None
        assert result["spam_score"] >= 70
        assert result["spam_label"] == "Known Telemarketer"

    def test_lookup_unknown_number(self, db_path):
        result = lookup_phone("+12125550199", db_path=db_path)
        assert result is None

    def test_lookup_all_sample_entries(self, db_path):
        sample_phones = [
            "+12025550101", "+12025550102",
            "+13105550171", "+13105550172",
            "+16175550193", "+16175550194",
            "+17135550187", "+17135550188",
            "+16025550131", "+16025550132",
        ]
        for phone in sample_phones:
            assert lookup_phone(phone, db_path=db_path) is not None, f"Missing: {phone}"


# ---------------------------------------------------------------------------
# Flask route tests
# ---------------------------------------------------------------------------

class TestRoutes:
    def test_index_returns_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"Reverse Phone" in resp.data

    def test_search_found_returns_rich_payload(self, client):
        resp = client.get("/search?phone=%2B12025550101")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["found"] is True
        r = data["result"]
        assert r["name"] == "Alice Johnson"
        assert r["age"] == 34
        assert r["line_type"] == "Cell"
        assert r["carrier"] == "AT&T"
        # email must be present as plain text — no modification by backend
        assert r["email"] == "alice.johnson@example.com"
        assert r["job_title"] == "Software Engineer"
        assert r["spam_score"] == 0

    def test_search_other_numbers_split_into_list(self, client):
        resp = client.get("/search?phone=%2B12025550101")
        data = resp.get_json()
        assert isinstance(data["result"]["other_numbers"], list)

    def test_search_relatives_split_into_list(self, client):
        resp = client.get("/search?phone=%2B12025550101")
        data = resp.get_json()
        assert isinstance(data["result"]["relatives"], list)
        assert "Bob Johnson" in data["result"]["relatives"]

    def test_search_found_without_plus_prefix(self, client):
        # US number without country code should be parsed as +1
        resp = client.get("/search?phone=2025550101")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["found"] is True
        assert data["result"]["name"] == "Alice Johnson"

    def test_search_not_found(self, client):
        # Valid US number not in sample data
        resp = client.get("/search?phone=2125550199")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["found"] is False

    def test_search_spam_number(self, client):
        resp = client.get("/search?phone=%2B18005551234")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["found"] is True
        assert data["result"]["spam_score"] >= 70

    def test_search_missing_phone(self, client):
        resp = client.get("/search?phone=")
        assert resp.status_code == 400
        data = resp.get_json()
        assert "error" in data

    def test_search_invalid_phone(self, client):
        resp = client.get("/search?phone=notaphone")
        assert resp.status_code == 400
        data = resp.get_json()
        assert "error" in data

    def test_search_no_param(self, client):
        resp = client.get("/search")
        assert resp.status_code == 400
        data = resp.get_json()
        assert "error" in data
