"""
Tests for the reverse phone search application.
"""
import pytest

from app import app as flask_app
from database import add_contact, init_db, lookup_phone


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


# ---------------------------------------------------------------------------
# add_contact database tests
# ---------------------------------------------------------------------------

class TestAddContact:
    def test_add_new_number_returns_true(self, db_path):
        added = add_contact("+17256002554", "Test User", db_path=db_path)
        assert added is True

    def test_add_duplicate_returns_false(self, db_path):
        add_contact("+17256002554", "Test User", db_path=db_path)
        added = add_contact("+17256002554", "Other User", db_path=db_path)
        assert added is False

    def test_add_number_is_retrievable(self, db_path):
        add_contact("+17256002554", "Jane Doe", db_path=db_path, city="Las Vegas", state="NV")
        result = lookup_phone("+17256002554", db_path=db_path)
        assert result is not None
        assert result["name"] == "Jane Doe"
        assert result["city"] == "Las Vegas"
        assert result["state"] == "NV"

    def test_add_number_unknown_fields_ignored(self, db_path):
        # Unknown kwargs should not raise; only allowed fields stored
        added = add_contact("+17256002554", "Jane Doe", db_path=db_path, unknown_field="x")
        assert added is True
        result = lookup_phone("+17256002554", db_path=db_path)
        assert result["name"] == "Jane Doe"


# ---------------------------------------------------------------------------
# /submit endpoint tests
# ---------------------------------------------------------------------------

class TestSubmitRoute:
    def test_submit_new_number(self, client):
        resp = client.post("/submit", json={"phone": "7256002554", "name": "Jane Doe"})
        assert resp.status_code == 200
        assert resp.get_json()["added"] is True

    def test_submit_lookup_after_add(self, client, db_path):
        client.post("/submit", json={"phone": "7256002554", "name": "Jane Doe", "city": "Las Vegas", "state": "NV"})
        result = lookup_phone("+17256002554", db_path=db_path)
        assert result is not None
        assert result["name"] == "Jane Doe"

    def test_submit_duplicate_returns_409(self, client):
        client.post("/submit", json={"phone": "7256002554", "name": "Jane Doe"})
        resp = client.post("/submit", json={"phone": "7256002554", "name": "Other Person"})
        assert resp.status_code == 409
        assert "error" in resp.get_json()

    def test_submit_missing_name_returns_400(self, client):
        resp = client.post("/submit", json={"phone": "7256002554"})
        assert resp.status_code == 400
        assert "error" in resp.get_json()

    def test_submit_invalid_phone_returns_400(self, client):
        resp = client.post("/submit", json={"phone": "notaphone", "name": "Jane Doe"})
        assert resp.status_code == 400
        assert "error" in resp.get_json()

    def test_submit_invalid_age_returns_400(self, client):
        resp = client.post("/submit", json={"phone": "7256002554", "name": "Jane Doe", "age": "notanumber"})
        assert resp.status_code == 400
        assert "error" in resp.get_json()

    def test_submit_with_optional_fields(self, client, db_path):
        resp = client.post("/submit", json={
            "phone": "7256002554", "name": "Jane Doe",
            "age": 30, "carrier": "AT&T", "city": "Las Vegas", "state": "NV",
        })
        assert resp.status_code == 200
        result = lookup_phone("+17256002554", db_path=db_path)
        assert result["age"] == 30
        assert result["carrier"] == "AT&T"
