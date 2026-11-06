from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_liveness_endpoint_returns_alive() -> None:
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_system_info_endpoint_returns_platform_identity() -> None:
    response = client.get("/api/v1/system/info")
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "CloudSec Range API"
    assert body["version"] == "0.4.0"


def test_domain_models_are_registered() -> None:
    from app.db.base import Base
    from app import models  # noqa: F401

    expected = {
        "curriculum_tracks",
        "curriculum_modules",
        "competencies",
        "learning_resources",
        "internship_tickets",
        "curriculum_versions",
        "curriculum_blocks",
        "curriculum_topics",
        "lessons",
        "labs",
        "assessments",
        "coverage_requirements",
        "competency_progress",
        "evidence",
        "ticket_competencies",
        "competency_prerequisites",
        "users", "roles", "permissions", "user_roles", "role_permissions",
        "auth_sessions", "audit_events",
    }
    assert expected.issubset(set(Base.metadata.tables))


def test_authentication_routes_are_registered_without_public_registration():
    schema = app.openapi()
    paths = schema["paths"]
    assert "/api/v1/auth/login" in paths
    assert "/api/v1/auth/me" in paths
    assert "/api/v1/auth/logout" in paths
    assert "/api/v1/auth/sessions" in paths
    assert "/api/v1/auth/sessions/{session_id}" in paths
    assert "/api/v1/auth/register" not in paths
    login_schema = schema["components"]["schemas"]["LoginRequest"]
    assert set(login_schema["properties"]) == {"email", "password"}
    auth_response_schema = schema["components"]["schemas"]["AuthResponse"]
    assert "csrf_token" in auth_response_schema["properties"]
    assert "access_token" not in auth_response_schema["properties"]
