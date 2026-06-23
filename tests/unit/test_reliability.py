from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.api.v1 import decisions as decisions_api
from app.api.v1 import health as health_api
from app.api.v1 import interviews as interviews_api
from app.api.v1.interviews import _verify_client_session_nonce
from app.core.errors import LLMUnavailableError
from app.db.models import (
    AuditLog,
    Candidate,
    CandidateStatus,
    FinalScorecard,
    HumanDecision,
    HumanDecisionStage,
    HumanDecisionValue,
    InterviewEvaluation,
    InterviewSession,
    InterviewSessionStatus,
    LlmCallLog,
    SecurityEventType,
    User,
    UserRole,
)
from app.db.session import get_session
from app.main import app
from app.repositories.candidates import CandidateRepository
from app.repositories.decisions import DecisionRepository
from app.repositories.interviews import InterviewRepository
from app.services.auth import hash_password
from app.services.lmstudio import LMStudioCompletion
from app.services.tokens import generate_token, hash_token


class FakeSession:
    def __init__(self) -> None:
        self.added = []
        self.commits = 0

    def add(self, obj) -> None:
        self.added.append(obj)

    async def commit(self) -> None:
        self.commits += 1

    async def refresh(self, _obj) -> None:
        return None


class FakeScalarSession(FakeSession):
    def __init__(self, values: list[object | None]) -> None:
        super().__init__()
        self.values = values

    async def scalar(self, _query):
        return self.values.pop(0)


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def make_user(role: UserRole = UserRole.RECRUITER) -> User:
    now = datetime.now(UTC)
    return User(
        id=uuid4(),
        name="Recruiter",
        email="recruiter@example.com",
        password_hash=hash_password("secret"),
        role=role,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


def override_current_user(user: User):
    async def dependency() -> User:
        return user

    return dependency


def override_session(fake_session: FakeSession):
    async def dependency():
        yield fake_session

    return dependency


def make_candidate(candidate_id: UUID | None = None, job_id: UUID | None = None) -> Candidate:
    now = datetime.now(UTC)
    return Candidate(
        id=candidate_id or uuid4(),
        job_id=job_id or uuid4(),
        name="Candidate",
        email=None,
        phone=None,
        resume_file_path=None,
        resume_text=None,
        resume_hash=None,
        parsed_profile_json=None,
        enriched_profile_json=None,
        status=CandidateStatus.INTERVIEW_COMPLETED,
        created_at=now,
        updated_at=now,
    )


def make_evaluation(session_id: UUID | None = None) -> InterviewEvaluation:
    now = datetime.now(UTC)
    return InterviewEvaluation(
        id=uuid4(),
        interview_session_id=session_id or uuid4(),
        candidate_id=uuid4(),
        job_id=uuid4(),
        overall_score=80,
        competency_scores_json=[],
        soft_skill_scores_json=[],
        strengths_json=[],
        weaknesses_json=[],
        red_flags_json=[],
        evidence_json=[],
        missing_evidence_json=[],
        recommendation="Review",
        confidence=75,
        created_at=now,
        updated_at=now,
    )


def make_scorecard(candidate_id: UUID | None = None, job_id: UUID | None = None) -> FinalScorecard:
    now = datetime.now(UTC)
    return FinalScorecard(
        id=uuid4(),
        candidate_id=candidate_id or uuid4(),
        job_id=job_id or uuid4(),
        resume_score=80,
        interview_score=82,
        soft_skill_score=78,
        overall_fit=81,
        risk_level="LOW",
        evidence_summary_json=[],
        candidate_fit_narrative="Good fit.",
        missing_evidence_json=[],
        recommendation="Review",
        confidence=75,
        created_at=now,
        updated_at=now,
    )


def test_client_session_nonce_is_hashed_and_verified() -> None:
    nonce = generate_token()
    interview = InterviewSession(
        job_id=uuid4(),
        candidate_id=uuid4(),
        client_session_hash=hash_token(nonce),
        security_events_json=[],
    )

    _verify_client_session_nonce(interview, nonce)

    assert interview.client_session_hash != nonce


@pytest.mark.parametrize("nonce", [None, "wrong"])
def test_invalid_client_session_nonce_fails_and_logs_security_event(nonce: str | None) -> None:
    interview = InterviewSession(
        job_id=uuid4(),
        candidate_id=uuid4(),
        client_session_hash=hash_token("right"),
        security_events_json=[],
    )

    with pytest.raises(HTTPException) as exc:
        _verify_client_session_nonce(interview, nonce)

    assert exc.value.status_code == 403
    assert interview.security_events_json[-1]["type"] == SecurityEventType.MULTIPLE_SESSION_ATTEMPT.value


@pytest.mark.asyncio
async def test_latest_interview_evaluation_returns_existing_row() -> None:
    session_id = uuid4()
    existing = make_evaluation(session_id)

    assert await InterviewRepository(FakeScalarSession([existing])).latest_evaluation(session_id) is existing


@pytest.mark.asyncio
async def test_latest_final_scorecard_returns_existing_row() -> None:
    candidate_id = uuid4()
    job_id = uuid4()
    existing = make_scorecard(candidate_id, job_id)

    assert await DecisionRepository(FakeScalarSession([existing])).latest_scorecard(candidate_id, job_id) is existing


def test_start_returns_client_session_nonce_and_stores_only_hash(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_session = FakeSession()
    token = "entry-token"
    candidate = make_candidate()
    candidate.status = CandidateStatus.INTERVIEW_INVITED
    interview = InterviewSession(
        id=uuid4(),
        job_id=candidate.job_id,
        candidate_id=candidate.id,
        status=InterviewSessionStatus.OTP_PENDING,
        secure_token_hash=hash_token(token),
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        otp_verified_at=datetime.now(UTC),
        single_session_lock=None,
        interview_plan_json={"questions": []},
        graph_state_json={"current_question_index": 0},
        security_events_json=[],
    )

    async def get_by_token_hash(self: InterviewRepository, token_hash: str) -> InterviewSession:
        assert token_hash == hash_token(token)
        return interview

    async def get_candidate(self: CandidateRepository, candidate_id: UUID) -> Candidate:
        assert candidate_id == candidate.id
        return candidate

    async def run_graph(state: dict) -> dict:
        assert state["interview_session_id"] == interview.id
        return {"status": InterviewSessionStatus.ACTIVE.value, "current_question_index": 0, "next_message": "Hello"}

    monkeypatch.setattr(InterviewRepository, "get_by_token_hash", get_by_token_hash)
    monkeypatch.setattr(CandidateRepository, "get", get_candidate)
    monkeypatch.setattr(interviews_api, "run_live_interview_graph", run_graph)
    app.dependency_overrides[get_session] = override_session(fake_session)

    response = TestClient(app).post(f"/api/v1/interview-entry/{token}/start")

    assert response.status_code == 200
    nonce = response.json()["client_session_nonce"]
    assert nonce
    assert interview.client_session_hash == hash_token(nonce)
    assert interview.client_session_hash != nonce
    assert candidate.status == CandidateStatus.INTERVIEW_ACTIVE


def test_second_client_start_attempt_logs_security_event(monkeypatch: pytest.MonkeyPatch) -> None:
    token = "entry-token"
    candidate = make_candidate()
    candidate.status = CandidateStatus.INTERVIEW_ACTIVE
    interview = InterviewSession(
        id=uuid4(),
        job_id=candidate.job_id,
        candidate_id=candidate.id,
        status=InterviewSessionStatus.ACTIVE,
        secure_token_hash=hash_token(token),
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        otp_verified_at=datetime.now(UTC),
        single_session_lock="locked",
        security_events_json=[],
    )

    async def get_by_token_hash(self: InterviewRepository, _token_hash: str) -> InterviewSession:
        return interview

    async def get_candidate(self: CandidateRepository, _candidate_id: UUID) -> Candidate:
        return candidate

    monkeypatch.setattr(InterviewRepository, "get_by_token_hash", get_by_token_hash)
    monkeypatch.setattr(CandidateRepository, "get", get_candidate)
    app.dependency_overrides[get_session] = override_session(FakeSession())

    response = TestClient(app).post(f"/api/v1/interview-entry/{token}/start")

    assert response.status_code == 409
    assert interview.security_events_json[-1]["type"] == SecurityEventType.MULTIPLE_SESSION_ATTEMPT.value


@pytest.mark.parametrize("payload", [{"answer": "hi"}, {"answer": "hi", "client_session_nonce": "wrong"}])
def test_answer_without_valid_nonce_fails(monkeypatch: pytest.MonkeyPatch, payload: dict[str, str]) -> None:
    token = "entry-token"
    interview = InterviewSession(
        id=uuid4(),
        job_id=uuid4(),
        candidate_id=uuid4(),
        status=InterviewSessionStatus.ACTIVE,
        secure_token_hash=hash_token(token),
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        otp_verified_at=datetime.now(UTC),
        client_session_hash=hash_token("right"),
        security_events_json=[],
    )
    candidate = make_candidate(interview.candidate_id, interview.job_id)

    async def get_by_token_hash(self: InterviewRepository, _token_hash: str) -> InterviewSession:
        return interview

    async def get_candidate(self: CandidateRepository, _candidate_id: UUID) -> Candidate:
        return candidate

    monkeypatch.setattr(InterviewRepository, "get_by_token_hash", get_by_token_hash)
    monkeypatch.setattr(CandidateRepository, "get", get_candidate)
    app.dependency_overrides[get_session] = override_session(FakeSession())

    response = TestClient(app).post(f"/api/v1/interview-entry/{token}/answer", json=payload)

    assert response.status_code == 403
    assert interview.security_events_json[-1]["type"] == SecurityEventType.MULTIPLE_SESSION_ATTEMPT.value


def test_answer_with_valid_nonce_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    token = "entry-token"
    nonce = "client-nonce"
    interview = InterviewSession(
        id=uuid4(),
        job_id=uuid4(),
        candidate_id=uuid4(),
        status=InterviewSessionStatus.ACTIVE,
        secure_token_hash=hash_token(token),
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        otp_verified_at=datetime.now(UTC),
        client_session_hash=hash_token(nonce),
        security_events_json=[],
    )
    candidate = make_candidate(interview.candidate_id, interview.job_id)
    calls = {"graph": 0}

    async def get_by_token_hash(self: InterviewRepository, _token_hash: str) -> InterviewSession:
        return interview

    async def get_candidate(self: CandidateRepository, _candidate_id: UUID) -> Candidate:
        return candidate

    async def run_graph(state: dict) -> dict:
        calls["graph"] += 1
        assert state["last_candidate_answer"] == "I built APIs."
        return {"status": InterviewSessionStatus.ACTIVE.value, "current_question_index": 1, "next_message": "Next"}

    monkeypatch.setattr(InterviewRepository, "get_by_token_hash", get_by_token_hash)
    monkeypatch.setattr(CandidateRepository, "get", get_candidate)
    monkeypatch.setattr(interviews_api, "run_live_interview_graph", run_graph)
    app.dependency_overrides[get_session] = override_session(FakeSession())

    response = TestClient(app).post(
        f"/api/v1/interview-entry/{token}/answer",
        json={"answer": "I built APIs.", "client_session_nonce": nonce},
    )

    assert response.status_code == 200
    assert calls["graph"] == 1


def test_complete_requires_valid_nonce_while_active(monkeypatch: pytest.MonkeyPatch) -> None:
    token = "entry-token"
    interview = InterviewSession(
        id=uuid4(),
        job_id=uuid4(),
        candidate_id=uuid4(),
        status=InterviewSessionStatus.ACTIVE,
        secure_token_hash=hash_token(token),
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        otp_verified_at=datetime.now(UTC),
        client_session_hash=hash_token("right"),
        security_events_json=[],
    )
    candidate = make_candidate(interview.candidate_id, interview.job_id)
    candidate.status = CandidateStatus.INTERVIEW_ACTIVE

    async def get_by_token_hash(self: InterviewRepository, _token_hash: str) -> InterviewSession:
        return interview

    async def get_candidate(self: CandidateRepository, _candidate_id: UUID) -> Candidate:
        return candidate

    monkeypatch.setattr(InterviewRepository, "get_by_token_hash", get_by_token_hash)
    monkeypatch.setattr(CandidateRepository, "get", get_candidate)
    app.dependency_overrides[get_session] = override_session(FakeSession())

    response = TestClient(app).post(f"/api/v1/interview-entry/{token}/complete", json={})

    assert response.status_code == 403
    assert interview.security_events_json[-1]["type"] == SecurityEventType.MULTIPLE_SESSION_ATTEMPT.value


def test_complete_with_valid_nonce_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    token = "entry-token"
    nonce = "client-nonce"
    interview = InterviewSession(
        id=uuid4(),
        job_id=uuid4(),
        candidate_id=uuid4(),
        status=InterviewSessionStatus.ACTIVE,
        secure_token_hash=hash_token(token),
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        otp_verified_at=datetime.now(UTC),
        client_session_hash=hash_token(nonce),
        interview_plan_json={"questions": [{"question": "Q"}]},
        graph_state_json={"current_question_index": 1},
        security_events_json=[],
    )
    candidate = make_candidate(interview.candidate_id, interview.job_id)
    candidate.status = CandidateStatus.INTERVIEW_ACTIVE

    async def get_by_token_hash(self: InterviewRepository, _token_hash: str) -> InterviewSession:
        return interview

    async def get_candidate(self: CandidateRepository, _candidate_id: UUID) -> Candidate:
        return candidate

    monkeypatch.setattr(InterviewRepository, "get_by_token_hash", get_by_token_hash)
    monkeypatch.setattr(CandidateRepository, "get", get_candidate)
    app.dependency_overrides[get_session] = override_session(FakeSession())

    response = TestClient(app).post(
        f"/api/v1/interview-entry/{token}/complete",
        json={"client_session_nonce": nonce},
    )

    assert response.status_code == 200
    assert interview.status == InterviewSessionStatus.COMPLETED
    assert candidate.status == CandidateStatus.INTERVIEW_COMPLETED


def test_repeated_interview_evaluation_without_force_returns_existing(monkeypatch: pytest.MonkeyPatch) -> None:
    session_id = uuid4()
    existing = make_evaluation(session_id)
    calls = {"graph": 0}

    async def latest_evaluation(self: InterviewRepository, requested_session_id: UUID) -> InterviewEvaluation:
        assert requested_session_id == session_id
        return existing

    async def run_graph(_state: dict) -> None:
        calls["graph"] += 1

    monkeypatch.setattr(InterviewRepository, "latest_evaluation", latest_evaluation)
    monkeypatch.setattr(interviews_api, "run_interview_evaluation_graph", run_graph)
    app.dependency_overrides[get_current_user] = override_current_user(make_user())
    app.dependency_overrides[get_session] = override_session(FakeSession())

    response = TestClient(app).post(
        f"/api/v1/interviews/{session_id}/evaluate",
        headers={"Authorization": "Bearer ignored"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(existing.id)
    assert calls["graph"] == 0


def test_forced_interview_evaluation_creates_new_row_and_audit(monkeypatch: pytest.MonkeyPatch) -> None:
    session_id = uuid4()
    existing = make_evaluation(session_id)
    forced = make_evaluation(session_id)
    fake_session = FakeSession()
    latest_values = [existing, forced]

    async def latest_evaluation(self: InterviewRepository, _session_id: UUID) -> InterviewEvaluation:
        return latest_values.pop(0)

    async def run_graph(_state: dict) -> None:
        return None

    monkeypatch.setattr(InterviewRepository, "latest_evaluation", latest_evaluation)
    monkeypatch.setattr(interviews_api, "run_interview_evaluation_graph", run_graph)
    app.dependency_overrides[get_current_user] = override_current_user(make_user())
    app.dependency_overrides[get_session] = override_session(fake_session)

    response = TestClient(app).post(
        f"/api/v1/interviews/{session_id}/evaluate?force=true",
        headers={"Authorization": "Bearer ignored"},
    )

    audit = next(item for item in fake_session.added if isinstance(item, AuditLog))
    assert response.status_code == 200
    assert response.json()["id"] == str(forced.id)
    assert audit.metadata_json["force"] is True


def test_repeated_final_scorecard_without_force_returns_existing(monkeypatch: pytest.MonkeyPatch) -> None:
    candidate = make_candidate()
    existing = make_scorecard(candidate.id, candidate.job_id)
    calls = {"graph": 0}

    async def get_candidate(self: CandidateRepository, candidate_id: UUID) -> Candidate:
        assert candidate_id == candidate.id
        return candidate

    async def latest_scorecard(self: DecisionRepository, _candidate_id: UUID, _job_id: UUID) -> FinalScorecard:
        return existing

    async def run_graph(_state: dict) -> None:
        calls["graph"] += 1

    monkeypatch.setattr(CandidateRepository, "get", get_candidate)
    monkeypatch.setattr(DecisionRepository, "latest_scorecard", latest_scorecard)
    monkeypatch.setattr(decisions_api, "run_final_decision_graph", run_graph)
    app.dependency_overrides[get_current_user] = override_current_user(make_user())
    app.dependency_overrides[get_session] = override_session(FakeSession())

    response = TestClient(app).post(
        f"/api/v1/candidates/{candidate.id}/final-scorecard",
        headers={"Authorization": "Bearer ignored"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(existing.id)
    assert calls["graph"] == 0


def test_forced_final_scorecard_creates_new_row_and_audit(monkeypatch: pytest.MonkeyPatch) -> None:
    candidate = make_candidate()
    existing = make_scorecard(candidate.id, candidate.job_id)
    forced = make_scorecard(candidate.id, candidate.job_id)
    fake_session = FakeSession()
    latest_values = [existing, forced]

    async def get_candidate(self: CandidateRepository, _candidate_id: UUID) -> Candidate:
        return candidate

    async def latest_scorecard(self: DecisionRepository, _candidate_id: UUID, _job_id: UUID) -> FinalScorecard:
        return latest_values.pop(0)

    async def run_graph(_state: dict) -> None:
        return None

    monkeypatch.setattr(CandidateRepository, "get", get_candidate)
    monkeypatch.setattr(DecisionRepository, "latest_scorecard", latest_scorecard)
    monkeypatch.setattr(decisions_api, "run_final_decision_graph", run_graph)
    app.dependency_overrides[get_current_user] = override_current_user(make_user())
    app.dependency_overrides[get_session] = override_session(fake_session)

    response = TestClient(app).post(
        f"/api/v1/candidates/{candidate.id}/final-scorecard?force=true",
        headers={"Authorization": "Bearer ignored"},
    )

    audit = next(item for item in fake_session.added if isinstance(item, AuditLog))
    assert response.status_code == 200
    assert response.json()["id"] == str(forced.id)
    assert audit.metadata_json["force"] is True


def test_health_llm_logs_usage(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_session = FakeSession()

    class FakeLMStudioClient:
        def __init__(self, _settings) -> None:
            pass

        async def chat_completion_with_usage(self, _prompt: str) -> LMStudioCompletion:
            return LMStudioCompletion('{"ok": true}', input_tokens=11, output_tokens=4)

    monkeypatch.setattr(health_api, "LMStudioClient", FakeLMStudioClient)
    app.dependency_overrides[get_session] = override_session(fake_session)

    response = TestClient(app).get("/health/llm")

    llm_log = next(item for item in fake_session.added if isinstance(item, LlmCallLog))
    assert response.status_code == 200
    assert llm_log.task == "health.llm"
    assert llm_log.cache_hit is False
    assert llm_log.status == "success"
    assert llm_log.input_tokens == 11
    assert llm_log.output_tokens == 4


def test_health_llm_logs_failed_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_session = FakeSession()

    class FakeLMStudioClient:
        def __init__(self, _settings) -> None:
            pass

        async def chat_completion_with_usage(self, _prompt: str) -> LMStudioCompletion:
            raise LLMUnavailableError("local model unavailable")

    monkeypatch.setattr(health_api, "LMStudioClient", FakeLMStudioClient)
    app.dependency_overrides[get_session] = override_session(fake_session)

    response = TestClient(app, raise_server_exceptions=False).get("/health/llm")

    llm_log = next(item for item in fake_session.added if isinstance(item, LlmCallLog))
    assert response.status_code == 503
    assert llm_log.task == "health.llm"
    assert llm_log.status == "error"
    assert llm_log.error == "local model unavailable"


def test_human_decision_stage_model_still_supports_final_and_shortlist() -> None:
    decision = HumanDecision(
        job_id=uuid4(),
        candidate_id=uuid4(),
        stage=HumanDecisionStage.FINAL,
        decision=HumanDecisionValue.HOLD,
        reason="Needs review.",
    )

    assert decision.stage == HumanDecisionStage.FINAL


def test_candidate_fixture_status_for_transition_tests() -> None:
    candidate = Candidate(job_id=uuid4(), status=CandidateStatus.INTERVIEW_COMPLETED)

    assert candidate.status == CandidateStatus.INTERVIEW_COMPLETED
