from app.db.base import Base
import app.models  # noqa: F401


def test_platform_core_tables_are_registered():
    expected = {
        "users", "roles", "permissions", "user_roles", "role_permissions",
        "auth_sessions", "audit_events",
    }
    assert expected.issubset(set(Base.metadata.tables))


def test_auth_sessions_do_not_store_raw_cookie_tokens():
    columns = set(Base.metadata.tables["auth_sessions"].columns.keys())
    assert "token_hash" in columns
    assert "csrf_token_hash" in columns
    assert "token" not in columns
    assert "raw_token" not in columns


def test_curriculum_api_rejects_requests_without_a_session():
    from fastapi.testclient import TestClient
    from app.main import app
    from app.db.session import get_db

    app.dependency_overrides[get_db] = lambda: None
    try:
        client = TestClient(app)
        response = client.get("/api/v1/curriculum/catalog")
        assert response.status_code == 401
        assert response.json()["detail"] == "Autenticação necessária."
    finally:
        app.dependency_overrides.clear()
