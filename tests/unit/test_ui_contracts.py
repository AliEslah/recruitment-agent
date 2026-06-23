from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.db.models import (
    Candidate,
    CandidateScore,
    CandidateStatus,
    InterviewEvaluation,
    InterviewMode,
    InterviewSession,
    InterviewSessionStatus,
    Job,
    JobStatus,
    User,
    UserRole,
)
from app.db.session import get_session
from app.main import app
from app.repositories.candidates import CandidateRepository
from app.repositories.interviews import InterviewRepository
from app.repositories.jobs import JobRepository
from app.repositories.logs import LogRepository
from app.services.email import EmailService
from app.services.auth import hash_password


class FakeSession:
    def __init__(self) -> None:
        self.added = []

    def add(self, obj) -> None:
        self.added.append(obj)

    async def commit(self) -> None:
        return None

    async def refresh(self, obj) -> None:
        return None


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


async def fake_session_dependency():
    yield FakeSession()


def override_current_user(role: UserRole = UserRole.RECRUITER):
    now = datetime.now(UTC)
    user = User(
        id=uuid4(),
        name="Test User",
        email=f"{role.value.lower()}@example.local",
        password_hash=hash_password("secret"),
        role=role,
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    async def dependency() -> User:
        return user

    return dependency


def make_candidate(candidate_id: UUID, job_id: UUID, *, status: CandidateStatus = CandidateStatus.SCORED) -> Candidate:
    now = datetime.now(UTC)
    return Candidate(
        id=candidate_id,
        job_id=job_id,
        name="Jane Backend",
        email="jane@example.local",
        phone=None,
        resume_file_path=None,
        resume_text="Resume",
        resume_hash="hash",
        parsed_profile_json={"skills": ["Python"]},
        enriched_profile_json=None,
        status=status,
        created_at=now,
        updated_at=now,
    )


def make_score(score_id: UUID, candidate_id: UUID, job_id: UUID, overall_score: float) -> CandidateScore:
    now = datetime.now(UTC)
    return CandidateScore(
        id=score_id,
        candidate_id=candidate_id,
        job_id=job_id,
        overall_score=overall_score,
        criteria_scores_json=[{"criterion_name": "Backend", "score": overall_score}],
        strengths_json=["FastAPI"],
        weaknesses_json=[],
        risks_json=[],
        evidence_json=[{"criterion": "Backend", "evidence": "Built APIs"}],
        recommendation="STRONG_MATCH",
        confidence=0.82,
        created_at=now,
        updated_at=now,
    )


def make_job(job_id: UUID) -> Job:
    now = datetime.now(UTC)
    return Job(
        id=job_id,
        title="Backend Engineer",
        department="Engineering",
        seniority="Senior",
        location="Remote",
        employment_type="Full-time",
        salary_range=None,
        raw_jd="Build APIs.",
        improved_jd=None,
        criteria_json=None,
        must_haves_json=None,
        nice_to_haves_json=None,
        disqualifiers_json=None,
        soft_skills_json=None,
        knockout_areas_json=None,
        status=JobStatus.APPROVED,
        created_by_id=None,
        created_at=now,
        updated_at=now,
    )


def make_interview(session_id: UUID, candidate_id: UUID, job_id: UUID) -> InterviewSession:
    now = datetime.now(UTC)
    return InterviewSession(
        id=session_id,
        job_id=job_id,
        candidate_id=candidate_id,
        mode=InterviewMode.CHAT,
        status=InterviewSessionStatus.INVITED,
        secure_token_hash="secret-token-hash",
        expires_at=now + timedelta(hours=24),
        started_at=None,
        ended_at=None,
        otp_hash="secret-otp-hash",
        otp_expires_at=None,
        otp_verified_at=None,
        single_session_lock="secret-lock",
        client_session_hash="secret-client-hash",
        interview_plan_json={"questions": [{"question": "Tell me about APIs."}]},
        graph_state_json={"internal": True},
        security_events_json=[{"event": "TOKEN_OPENED"}],
        created_at=now,
        updated_at=now,
    )


def make_evaluation(evaluation_id: UUID, interview_session_id: UUID, candidate_id: UUID, job_id: UUID) -> InterviewEvaluation:
    now = datetime.now(UTC)
    return InterviewEvaluation(
        id=evaluation_id,
        interview_session_id=interview_session_id,
        candidate_id=candidate_id,
        job_id=job_id,
        overall_score=0.8,
        competency_scores_json={"backend": 0.8},
        soft_skill_scores_json={"communication": 0.7},
        strengths_json=["Clear examples"],
        weaknesses_json=[],
        red_flags_json=[],
        evidence_json={"backend": "Discussed FastAPI"},
        missing_evidence_json=[],
        recommendation="Proceed",
        confidence=0.75,
        created_at=now,
        updated_at=now,
    )


def test_latest_candidate_score_endpoint_returns_latest_score(monkeypatch: pytest.MonkeyPatch) -> None:
    candidate_id = uuid4()
    job_id = uuid4()
    score = make_score(uuid4(), candidate_id, job_id, 0.91)

    async def fake_get(self, requested_candidate_id: UUID):
        assert requested_candidate_id == candidate_id
        return make_candidate(candidate_id, job_id)

    async def fake_latest_score(self, requested_candidate_id: UUID, requested_job_id: UUID):
        assert requested_candidate_id == candidate_id
        assert requested_job_id == job_id
        return score

    monkeypatch.setattr(CandidateRepository, "get", fake_get)
    monkeypatch.setattr(CandidateRepository, "latest_score", fake_latest_score)
    app.dependency_overrides[get_current_user] = override_current_user()
    app.dependency_overrides[get_session] = fake_session_dependency
    client = TestClient(app)

    response = client.get(f"/api/v1/candidates/{candidate_id}/score/latest", headers={"Authorization": "Bearer test"})

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(score.id)
    assert body["candidate_id"] == str(candidate_id)
    assert body["overall_score"] == 0.91
    assert body["recommendation"] == "STRONG_MATCH"


def test_candidate_list_exposes_latest_score_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    job_id = uuid4()
    candidate_id = uuid4()
    candidate = make_candidate(candidate_id, job_id)
    score = make_score(uuid4(), candidate_id, job_id, 0.87)

    async def fake_job_get(self, requested_job_id: UUID):
        assert requested_job_id == job_id
        return make_job(job_id)

    async def fake_list_for_job(self, requested_job_id: UUID):
        assert requested_job_id == job_id
        return [candidate]

    async def fake_latest_scores_for_job(self, requested_job_id: UUID):
        assert requested_job_id == job_id
        return {candidate_id: score}

    monkeypatch.setattr(JobRepository, "get", fake_job_get)
    monkeypatch.setattr(CandidateRepository, "list_for_job", fake_list_for_job)
    monkeypatch.setattr(CandidateRepository, "latest_scores_for_job", fake_latest_scores_for_job)
    app.dependency_overrides[get_current_user] = override_current_user()
    app.dependency_overrides[get_session] = fake_session_dependency
    client = TestClient(app)

    response = client.get(f"/api/v1/jobs/{job_id}/candidates", headers={"Authorization": "Bearer test"})

    assert response.status_code == 200
    body = response.json()
    assert body[0]["id"] == str(candidate_id)
    assert body[0]["latest_score"]["overall_score"] == 0.87
    assert body[0]["latest_score"]["recommendation"] == "STRONG_MATCH"
    assert body[0]["latest_score"]["confidence"] == 0.82


def test_candidate_score_endpoint_blocks_unauthenticated_access() -> None:
    client = TestClient(app)

    response = client.get(f"/api/v1/candidates/{uuid4()}/score/latest")

    assert response.status_code == 401


def test_resume_upload_invalid_form_email_returns_422() -> None:
    app.dependency_overrides[get_current_user] = override_current_user()
    app.dependency_overrides[get_session] = fake_session_dependency
    client = TestClient(app)

    response = client.post(
        f"/api/v1/jobs/{uuid4()}/candidates/upload-resume",
        headers={"Authorization": "Bearer test"},
        data={"name": "Jane", "email": "jane@example.local"},
        files={"file": ("resume.txt", b"Resume", "text/plain")},
    )

    assert response.status_code == 422


def test_candidate_interview_list_returns_sessions_without_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    candidate_id = uuid4()
    job_id = uuid4()
    session_id = uuid4()
    interview = make_interview(session_id, candidate_id, job_id)
    evaluation = make_evaluation(uuid4(), session_id, candidate_id, job_id)

    async def fake_candidate_get(self, requested_candidate_id: UUID):
        assert requested_candidate_id == candidate_id
        return make_candidate(candidate_id, job_id)

    async def fake_list_for_candidate(self, requested_candidate_id: UUID):
        assert requested_candidate_id == candidate_id
        return [interview]

    async def fake_latest_evaluations_for_sessions(self, session_ids: list[UUID]):
        assert session_ids == [session_id]
        return {session_id: evaluation}

    monkeypatch.setattr(CandidateRepository, "get", fake_candidate_get)
    monkeypatch.setattr(InterviewRepository, "list_for_candidate", fake_list_for_candidate)
    monkeypatch.setattr(InterviewRepository, "latest_evaluations_for_sessions", fake_latest_evaluations_for_sessions)
    app.dependency_overrides[get_current_user] = override_current_user()
    app.dependency_overrides[get_session] = fake_session_dependency
    client = TestClient(app)

    response = client.get(f"/api/v1/candidates/{candidate_id}/interviews", headers={"Authorization": "Bearer test"})

    assert response.status_code == 200
    body = response.json()
    assert body[0]["id"] == str(session_id)
    assert body[0]["question_count"] == 1
    assert body[0]["evaluation_status"] == "EVALUATED"
    serialized = str(body)
    assert "secure_token_hash" not in serialized
    assert "otp_hash" not in serialized
    assert "client_session_hash" not in serialized
    assert "secret-token-hash" not in serialized
    assert "secret-otp-hash" not in serialized
    assert "secret-client-hash" not in serialized


def test_candidate_interview_list_blocks_unauthenticated_access() -> None:
    client = TestClient(app)

    response = client.get(f"/api/v1/candidates/{uuid4()}/interviews")

    assert response.status_code == 401


def test_send_invite_email_uses_frontend_candidate_route(monkeypatch: pytest.MonkeyPatch) -> None:
    candidate_id = uuid4()
    job_id = uuid4()
    session_id = uuid4()
    interview = make_interview(session_id, candidate_id, job_id)
    candidate = make_candidate(candidate_id, job_id, status=CandidateStatus.SHORTLISTED)
    sent_email: dict[str, object] = {}

    async def fake_get_session(self, requested_session_id: UUID):
        assert requested_session_id == session_id
        return interview

    async def fake_candidate_get(self, requested_candidate_id: UUID):
        assert requested_candidate_id == candidate_id
        return candidate

    async def fake_send(self, **kwargs):
        sent_email.update(kwargs)

    async def fake_audit(self, log):
        return log

    monkeypatch.setattr(InterviewRepository, "get_session", fake_get_session)
    monkeypatch.setattr(CandidateRepository, "get", fake_candidate_get)
    monkeypatch.setattr(EmailService, "send", fake_send)
    monkeypatch.setattr(LogRepository, "audit", fake_audit)
    monkeypatch.setattr("app.api.v1.interviews.generate_token", lambda: "raw-token-value")
    app.dependency_overrides[get_current_user] = override_current_user()
    app.dependency_overrides[get_session] = fake_session_dependency
    client = TestClient(app)

    response = client.post(f"/api/v1/interviews/{session_id}/send-invite", headers={"Authorization": "Bearer test"})

    assert response.status_code == 200
    assert "http://localhost:3000/candidate/interview/raw-token-value" in str(sent_email["body"])
    assert "/api/v1/interview-entry/raw-token-value" not in str(sent_email["body"])
    assert sent_email["secrets_to_redact"][0].value == "raw-token-value"
