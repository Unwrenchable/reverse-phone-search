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
    def test_lookup_known_number(self, db_path):
        result = lookup_phone("+12025550101", db_path=db_path)
        assert result is not None
        assert result["name"] == "Alice Johnson"
        assert result["city"] == "Washington"
        assert result["state"] == "DC"

    def test_lookup_unknown_number(self, db_path):
        result = lookup_phone("+19999999999", db_path=db_path)
        assert result is None

    def test_lookup_all_sample_entries(self, db_path):
        sample_phones = [
            "+12025550101",
            "+12025550102",
            "+13105550171",
            "+16175550193",
            "+17135550187",
            "+16025550132",
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
        assert b"Reverse Phone Search" in resp.data

    def test_search_found(self, client):
        resp = client.get("/search?phone=%2B12025550101")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["found"] is True
        assert data["result"]["name"] == "Alice Johnson"

    def test_search_found_without_plus_prefix(self, client):
        # US number without country code should be parsed as +1
        resp = client.get("/search?phone=2025550101")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["found"] is True
        assert data["result"]["name"] == "Alice Johnson"

    def test_search_not_found(self, client):
        # Valid US number that is not in the sample data
        resp = client.get("/search?phone=2125550199")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["found"] is False

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
