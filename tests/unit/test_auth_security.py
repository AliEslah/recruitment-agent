from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.db.models import AuditLog, Candidate, CandidateStatus, HumanDecision, Job, JobStatus, User, UserRole
from app.db.session import get_session
from app.main import app
from app.repositories.candidates import CandidateRepository
from app.repositories.jobs import JobRepository
from app.repositories.logs import LogRepository
from app.services.auth import create_access_token, decode_access_token, hash_password, verify_password


class FakeSession:
    def __init__(self) -> None:
        self.added = []

    def add(self, obj) -> None:
        self.added.append(obj)

    async def commit(self) -> None:
        return None

    async def refresh(self, obj) -> None:
        return None


def make_user(role: UserRole = UserRole.RECRUITER) -> User:
    now = datetime.now(UTC)
    return User(
        id=uuid4(),
        name=f"{role.value.title()} User",
        email=f"{role.value.lower()}@example.com",
        password_hash=hash_password("secret"),
        role=role,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def override_current_user(user: User):
    async def dependency() -> User:
        return user

    return dependency


def test_password_hash_and_jwt_round_trip() -> None:
    password_hash = hash_password("correct horse battery staple")

    assert verify_password("correct horse battery staple", password_hash)
    assert not verify_password("wrong", password_hash)

    user_id = str(uuid4())
    token = create_access_token(user_id, extra_claims={"role": UserRole.ADMIN.value})
    payload = decode_access_token(token)

    assert payload["sub"] == user_id
    assert payload["role"] == UserRole.ADMIN.value


def test_unauthenticated_job_endpoint_returns_401() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/jobs")

    assert response.status_code == 401


def test_unauthenticated_admin_endpoint_returns_401() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/admin/audit")

    assert response.status_code == 401


def test_recruiter_cannot_access_admin_endpoint() -> None:
    app.dependency_overrides[get_current_user] = override_current_user(make_user(UserRole.RECRUITER))
    client = TestClient(app)

    response = client.get("/api/v1/admin/audit", headers={"Authorization": "Bearer ignored"})

    assert response.status_code == 403


def test_admin_can_access_admin_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    async def empty_audit_logs(self, limit: int = 100):
        return []

    monkeypatch.setattr(LogRepository, "audit_logs", empty_audit_logs)
    app.dependency_overrides[get_current_user] = override_current_user(make_user(UserRole.ADMIN))
    client = TestClient(app)

    response = client.get("/api/v1/admin/audit", headers={"Authorization": "Bearer ignored"})

    assert response.status_code == 200
    assert response.json() == []


def test_authenticated_recruiter_can_create_job(monkeypatch: pytest.MonkeyPatch) -> None:
    recruiter = make_user(UserRole.RECRUITER)
    captured = {}
    now = datetime.now(UTC)

    async def create_job(self, payload):
        captured["created_by_id"] = payload.created_by_id
        return Job(
            id=uuid4(),
            title=payload.title,
            department=payload.department,
            seniority=payload.seniority,
            location=payload.location,
            employment_type=payload.employment_type,
            salary_range=payload.salary_range,
            raw_jd=payload.raw_jd,
            improved_jd=None,
            criteria_json=None,
            must_haves_json=None,
            nice_to_haves_json=None,
            disqualifiers_json=None,
            soft_skills_json=None,
            knockout_areas_json=None,
            status=JobStatus.DRAFT,
            created_by_id=payload.created_by_id,
            created_at=now,
            updated_at=now,
        )

    monkeypatch.setattr(JobRepository, "create", create_job)
    app.dependency_overrides[get_current_user] = override_current_user(recruiter)
    client = TestClient(app)

    response = client.post(
        "/api/v1/jobs",
        headers={"Authorization": "Bearer ignored"},
        json={"title": "Backend Engineer", "raw_jd": "Build APIs."},
    )

    assert response.status_code == 200
    assert captured["created_by_id"] == recruiter.id
    assert response.json()["created_by_id"] == str(recruiter.id)


def test_human_decision_uses_authenticated_user(monkeypatch: pytest.MonkeyPatch) -> None:
    recruiter = make_user(UserRole.HIRING_MANAGER)
    fake_session = FakeSession()
    candidate_id = uuid4()
    job_id = uuid4()
    now = datetime.now(UTC)
    candidate = Candidate(
        id=candidate_id,
        job_id=job_id,
        name="Candidate",
        email="candidate@example.com",
        phone=None,
        resume_file_path=None,
        resume_text=None,
        resume_hash=None,
        parsed_profile_json=None,
        enriched_profile_json=None,
        status=CandidateStatus.SCORED,
        created_at=now,
        updated_at=now,
    )

    async def fake_get(self, requested_candidate_id):
        assert requested_candidate_id == candidate_id
        return candidate

    async def fake_session_dependency():
        yield fake_session

    monkeypatch.setattr(CandidateRepository, "get", fake_get)
    app.dependency_overrides[get_current_user] = override_current_user(recruiter)
    app.dependency_overrides[get_session] = fake_session_dependency
    client = TestClient(app)

    response = client.post(
        f"/api/v1/candidates/{candidate_id}/shortlist-decision",
        headers={"Authorization": "Bearer ignored"},
        json={"decision": "APPROVE", "reason": "Good fit.", "user_id": str(uuid4())},
    )

    assert response.status_code == 200
    decisions = [item for item in fake_session.added if isinstance(item, HumanDecision)]
    audits = [item for item in fake_session.added if isinstance(item, AuditLog)]
    assert decisions[0].user_id == recruiter.id
    assert audits[0].actor_user_id == recruiter.id


def test_candidate_interview_entry_remains_public(monkeypatch: pytest.MonkeyPatch) -> None:
    async def missing_token(self, token_hash: str):
        from app.core.errors import NotFoundError

        raise NotFoundError("Interview token not found.")

    async def fake_session_dependency():
        yield FakeSession()

    from app.repositories.interviews import InterviewRepository

    monkeypatch.setattr(InterviewRepository, "get_by_token_hash", missing_token)
    app.dependency_overrides[get_session] = fake_session_dependency
    client = TestClient(app)

    response = client.get("/api/v1/interview-entry/not-real")

    assert response.status_code == 404
    assert response.json()["detail"] == "Interview token not found."
