from __future__ import annotations

import json
from datetime import UTC, datetime
from importlib.resources import files
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.db.models import InterviewMode, InterviewSession, InterviewSessionStatus, PilotFeedback, User, UserRole
from app.db.session import get_session
from app.evaluation.quality import scan_protected_terms
from app.main import app
from app.repositories.feedback import FeedbackRepository
from app.repositories.interviews import InterviewRepository
from app.scripts.seed_pilot_data import find_forbidden_ai_output_keys
from app.services.auth import hash_password
from app.services.role_templates import get_role_template, load_role_templates


class FakeSession:
    def __init__(self) -> None:
        self.added = []

    def add(self, obj) -> None:
        if getattr(obj, "id", None) is None:
            obj.id = uuid4()
        if getattr(obj, "created_at", None) is None:
            obj.created_at = datetime.now(UTC)
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


def make_user(role: UserRole = UserRole.RECRUITER) -> User:
    now = datetime.now(UTC)
    return User(
        id=uuid4(),
        name=f"{role.value.title()} User",
        email=f"{role.value.lower()}@example.local",
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


async def fake_session_dependency():
    yield FakeSession()


def load_fixture(name: str):
    return json.loads(files("app.fixtures").joinpath(name).read_text(encoding="utf-8"))


def test_role_templates_load_requested_pilot_roles() -> None:
    templates = load_role_templates()
    template_ids = {template.template_id for template in templates}

    assert {
        "sales_account_executive",
        "customer_support_specialist",
        "operations_manager",
        "hr_generalist",
        "marketing_specialist",
        "finance_analyst",
        "backend_engineer",
    }.issubset(template_ids)
    assert get_role_template("backend_engineer").raw_jd_starter


def test_question_bank_seed_avoids_protected_attribute_questions() -> None:
    questions = load_fixture("question_bank_items.json")

    warnings = scan_protected_terms(questions, location="question_bank")

    assert warnings == []


def test_pilot_seed_fixtures_do_not_contain_fake_ai_outputs() -> None:
    payload = [
        load_fixture("role_templates.json"),
        load_fixture("question_bank_items.json"),
        load_fixture("pilot_seed_candidates.json"),
    ]

    assert find_forbidden_ai_output_keys(payload) == []


def test_feedback_endpoint_requires_auth() -> None:
    client = TestClient(app)

    response = client.post("/api/v1/feedback", json={"feedback_type": "GENERAL_FEEDBACK", "rating": 5})

    assert response.status_code == 401


def test_authenticated_feedback_records_current_user(monkeypatch: pytest.MonkeyPatch) -> None:
    recruiter = make_user(UserRole.RECRUITER)
    fake_session = FakeSession()

    async def session_dependency():
        yield fake_session

    app.dependency_overrides[get_current_user] = override_current_user(recruiter)
    app.dependency_overrides[get_session] = session_dependency
    client = TestClient(app)

    response = client.post(
        "/api/v1/feedback",
        headers={"Authorization": "Bearer ignored"},
        json={
            "candidate_id": str(uuid4()),
            "job_id": str(uuid4()),
            "feedback_type": "RECRUITER_SCORECARD_FEEDBACK",
            "rating": 4,
            "comment": "Useful but needs clearer missing evidence.",
        },
    )

    assert response.status_code == 200
    feedback = next(item for item in fake_session.added if isinstance(item, PilotFeedback))
    assert feedback.user_id == recruiter.id
    assert feedback.feedback_type == "RECRUITER_SCORECARD_FEEDBACK"


def test_admin_feedback_requires_admin() -> None:
    app.dependency_overrides[get_current_user] = override_current_user(make_user(UserRole.RECRUITER))
    client = TestClient(app)

    response = client.get("/api/v1/admin/feedback", headers={"Authorization": "Bearer ignored"})

    assert response.status_code == 403


def test_admin_feedback_allows_admin(monkeypatch: pytest.MonkeyPatch) -> None:
    async def empty_feedback(self: FeedbackRepository, limit: int = 100):
        return []

    monkeypatch.setattr(FeedbackRepository, "list_recent", empty_feedback)
    app.dependency_overrides[get_current_user] = override_current_user(make_user(UserRole.ADMIN))
    client = TestClient(app)

    response = client.get("/api/v1/admin/feedback", headers={"Authorization": "Bearer ignored"})

    assert response.status_code == 200
    assert response.json() == []


def make_completed_interview(session_id: UUID, candidate_id: UUID, job_id: UUID) -> InterviewSession:
    now = datetime.now(UTC)
    return InterviewSession(
        id=session_id,
        job_id=job_id,
        candidate_id=candidate_id,
        mode=InterviewMode.CHAT,
        status=InterviewSessionStatus.COMPLETED,
        secure_token_hash="hash",
        expires_at=now,
        started_at=now,
        ended_at=now,
        otp_hash=None,
        otp_expires_at=None,
        otp_verified_at=now,
        single_session_lock=None,
        client_session_hash=None,
        interview_plan_json=None,
        graph_state_json=None,
        security_events_json=None,
        created_at=now,
        updated_at=now,
    )


def test_candidate_feedback_public_after_completion(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_session = FakeSession()
    session_id = uuid4()
    candidate_id = uuid4()
    job_id = uuid4()

    async def session_dependency():
        yield fake_session

    async def completed_by_token(self: InterviewRepository, token_hash: str):
        return make_completed_interview(session_id, candidate_id, job_id)

    monkeypatch.setattr(InterviewRepository, "get_by_token_hash", completed_by_token)
    app.dependency_overrides[get_session] = session_dependency
    client = TestClient(app)

    response = client.post("/api/v1/interview-entry/raw-token/feedback", json={"rating": 5, "comment": "Clear flow."})

    assert response.status_code == 200
    feedback = next(item for item in fake_session.added if isinstance(item, PilotFeedback))
    assert feedback.user_id is None
    assert feedback.candidate_id == candidate_id
    assert feedback.job_id == job_id
    assert feedback.interview_session_id == session_id
    assert feedback.feedback_type == "CANDIDATE_INTERVIEW_FEEDBACK"


def test_candidate_feedback_rejects_incomplete_interview(monkeypatch: pytest.MonkeyPatch) -> None:
    async def active_by_token(self: InterviewRepository, token_hash: str):
        interview = make_completed_interview(uuid4(), uuid4(), uuid4())
        interview.status = InterviewSessionStatus.ACTIVE
        return interview

    monkeypatch.setattr(InterviewRepository, "get_by_token_hash", active_by_token)
    app.dependency_overrides[get_session] = fake_session_dependency
    client = TestClient(app)

    response = client.post("/api/v1/interview-entry/raw-token/feedback", json={"rating": 3})

    assert response.status_code == 409
