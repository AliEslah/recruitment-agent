from __future__ import annotations

from uuid import uuid4

import pytest

from app.agents.interview.planning_graph import load_context
from app.core.errors import ConflictError
from app.db.models import Candidate, CandidateStatus, InterviewSession, InterviewSessionStatus, Job, JobStatus
from app.repositories.candidates import CandidateRepository
from app.services.status_transitions import transition_candidate, transition_interview, transition_job


def test_valid_status_transitions() -> None:
    job = Job(title="Role", raw_jd="JD", status=JobStatus.DRAFT)
    transition_job(job, JobStatus.CRITERIA_GENERATED)
    transition_job(job, JobStatus.APPROVED)

    candidate = Candidate(job_id=uuid4(), status=CandidateStatus.UPLOADED)
    transition_candidate(candidate, CandidateStatus.SCORED)
    transition_candidate(candidate, CandidateStatus.SHORTLISTED)

    interview = InterviewSession(
        job_id=uuid4(),
        candidate_id=uuid4(),
        status=InterviewSessionStatus.DRAFT,
    )
    transition_interview(interview, InterviewSessionStatus.INVITED)
    transition_interview(interview, InterviewSessionStatus.OTP_PENDING)
    transition_interview(interview, InterviewSessionStatus.ACTIVE)
    transition_interview(interview, InterviewSessionStatus.COMPLETED)


def test_invalid_candidate_transition_fails() -> None:
    candidate = Candidate(job_id=uuid4(), status=CandidateStatus.REJECTED)

    with pytest.raises(ConflictError, match="REJECTED -> SHORTLISTED"):
        transition_candidate(candidate, CandidateStatus.SHORTLISTED)


def test_invalid_interview_transition_fails() -> None:
    interview = InterviewSession(
        job_id=uuid4(),
        candidate_id=uuid4(),
        status=InterviewSessionStatus.COMPLETED,
    )

    with pytest.raises(ConflictError, match="COMPLETED -> ACTIVE"):
        transition_interview(interview, InterviewSessionStatus.ACTIVE)


def test_approving_criteria_before_generation_fails() -> None:
    job = Job(title="Role", raw_jd="JD", status=JobStatus.DRAFT)

    with pytest.raises(ConflictError, match="DRAFT -> APPROVED"):
        transition_job(job, JobStatus.APPROVED)


@pytest.mark.asyncio
async def test_interview_plan_for_non_shortlisted_candidate_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    candidate = Candidate(id=uuid4(), job_id=uuid4(), status=CandidateStatus.SCORED)

    async def fake_get(self: CandidateRepository, candidate_id):
        assert candidate_id == candidate.id
        return candidate

    monkeypatch.setattr(CandidateRepository, "get", fake_get)

    with pytest.raises(ConflictError, match="SHORTLISTED"):
        await load_context({"session": object(), "candidate_id": candidate.id, "job_id": candidate.job_id})
