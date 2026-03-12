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

    def test_lookup_expanded_entries(self, db_path):
        """Verify entries added in the expanded database across multiple area codes."""
        expanded_phones = [
            "+17256002554",  # Las Vegas, NV (725)
            "+17026002101",  # Las Vegas, NV (702)
            "+12125550201",  # New York, NY
            "+13125550501",  # Chicago, IL
            "+14045552201",  # Atlanta, GA
            "+13055552401",  # Miami, FL
            "+14155551601",  # San Francisco, CA
            "+12065551801",  # Seattle, WA
        ]
        for phone in expanded_phones:
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
# search_count increment tests
# ---------------------------------------------------------------------------

class TestSearchCount:
    def test_search_count_increments_on_lookup(self, db_path):
        """lookup_phone must increment search_count each time it is called."""
        from database import lookup_phone
        r1 = lookup_phone("+12025550101", db_path=db_path)
        count_before = r1["search_count"]
        r2 = lookup_phone("+12025550101", db_path=db_path)
        assert r2["search_count"] == count_before + 1

    def test_search_count_increments_via_route(self, client, db_path):
        """The /search route must cause search_count to grow."""
        from database import lookup_phone
        before = lookup_phone("+12025550101", db_path=db_path)["search_count"]
        client.get("/search?phone=%2B12025550101")
        after = lookup_phone("+12025550101", db_path=db_path)["search_count"]
        assert after > before

    def test_search_count_not_incremented_for_unknown(self, db_path):
        """lookup_phone must not error and must return None for unknown numbers."""
        from database import lookup_phone
        result = lookup_phone("+12125550199", db_path=db_path)
        assert result is None


# ---------------------------------------------------------------------------
# Rate limiting tests
# ---------------------------------------------------------------------------

class TestRateLimiting:
    def test_rate_limit_returns_429_after_max_requests(self, app, monkeypatch):
        """Exceed RATE_LIMIT_MAX_CALLS within the window → 429."""
        import app as app_module
        # Patch limits so we can trigger them quickly
        monkeypatch.setattr(app_module, "_RATE_LIMIT_MAX_CALLS", 3)
        # Clear any existing rate data
        monkeypatch.setattr(app_module, "_rate_data", {})
        client = app.test_client()
        for _ in range(3):
            resp = client.get("/search?phone=2025550101")
            assert resp.status_code != 429
        # 4th request should be rate-limited
        resp = client.get("/search?phone=2025550101")
        assert resp.status_code == 429
        data = resp.get_json()
        assert "error" in data

    def test_rate_limit_resets_after_window(self, app, monkeypatch):
        """After the window expires, requests are allowed again."""
        import app as app_module
        import time
        monkeypatch.setattr(app_module, "_RATE_LIMIT_MAX_CALLS", 2)
        monkeypatch.setattr(app_module, "_RATE_LIMIT_WINDOW", 1)
        monkeypatch.setattr(app_module, "_rate_data", {})
        client = app.test_client()
        for _ in range(2):
            client.get("/search?phone=2025550101")
        # Exhaust limit
        resp = client.get("/search?phone=2025550101")
        assert resp.status_code == 429
        # Wait for window to expire
        time.sleep(1.1)
        resp = client.get("/search?phone=2025550101")
        assert resp.status_code != 429
