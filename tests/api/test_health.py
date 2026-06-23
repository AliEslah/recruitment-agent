from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_health_check() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "AI Recruiting Decision Platform"}


def test_openapi_contains_required_routes() -> None:
    schema = app.openapi()

    for path in [
        "/health/llm",
        "/api/v1/jobs",
        "/api/v1/jobs/{job_id}/calibrate",
        "/api/v1/candidates/{candidate_id}/process",
        "/api/v1/candidates/{candidate_id}/score/latest",
        "/api/v1/candidates/{candidate_id}/interviews",
        "/api/v1/interview-entry/{token}/answer",
        "/api/v1/candidates/{candidate_id}/final-decision",
    ]:
        assert path in schema["paths"]


def test_openapi_admin_communications_exposes_redacted_body() -> None:
    schema = app.openapi()

    communication_log_schema = schema["components"]["schemas"]["CommunicationLogRead"]

    assert "body" in communication_log_schema["properties"]
    assert "body" in communication_log_schema["required"]
