from __future__ import annotations

from enum import Enum
from typing import TypeVar

from app.core.errors import ConflictError
from app.db.models import CandidateStatus, InterviewSessionStatus, JobStatus

StatusT = TypeVar("StatusT", bound=Enum)


ALLOWED_JOB_TRANSITIONS: dict[JobStatus, set[JobStatus]] = {
    JobStatus.DRAFT: {JobStatus.CRITERIA_GENERATED},
    JobStatus.CRITERIA_GENERATED: {JobStatus.APPROVED, JobStatus.CRITERIA_GENERATED},
    JobStatus.APPROVED: {JobStatus.CLOSED},
    JobStatus.CLOSED: set(),
}

ALLOWED_CANDIDATE_TRANSITIONS: dict[CandidateStatus, set[CandidateStatus]] = {
    CandidateStatus.UPLOADED: {CandidateStatus.PARSED, CandidateStatus.SCORED, CandidateStatus.NEEDS_REVIEW},
    CandidateStatus.PARSED: {CandidateStatus.SCORED, CandidateStatus.NEEDS_REVIEW},
    CandidateStatus.SCORED: {CandidateStatus.SHORTLISTED, CandidateStatus.REJECTED, CandidateStatus.NEEDS_REVIEW},
    CandidateStatus.NEEDS_REVIEW: {
        CandidateStatus.SHORTLISTED,
        CandidateStatus.REJECTED,
        CandidateStatus.SCORED,
        CandidateStatus.FINAL_REVIEW,
    },
    CandidateStatus.SHORTLISTED: {CandidateStatus.INTERVIEW_INVITED, CandidateStatus.REJECTED},
    CandidateStatus.REJECTED: set(),
    CandidateStatus.INTERVIEW_INVITED: {CandidateStatus.INTERVIEW_ACTIVE},
    CandidateStatus.INTERVIEW_ACTIVE: {CandidateStatus.INTERVIEW_COMPLETED},
    CandidateStatus.INTERVIEW_COMPLETED: {
        CandidateStatus.FINAL_REVIEW,
        CandidateStatus.APPROVED,
        CandidateStatus.REJECTED_FINAL,
    },
    CandidateStatus.FINAL_REVIEW: {CandidateStatus.APPROVED, CandidateStatus.REJECTED_FINAL},
    CandidateStatus.APPROVED: set(),
    CandidateStatus.REJECTED_FINAL: set(),
}

ALLOWED_INTERVIEW_TRANSITIONS: dict[InterviewSessionStatus, set[InterviewSessionStatus]] = {
    InterviewSessionStatus.DRAFT: {InterviewSessionStatus.INVITED, InterviewSessionStatus.ACTIVE, InterviewSessionStatus.CANCELLED},
    InterviewSessionStatus.INVITED: {
        InterviewSessionStatus.OTP_PENDING,
        InterviewSessionStatus.ACTIVE,
        InterviewSessionStatus.EXPIRED,
        InterviewSessionStatus.CANCELLED,
    },
    InterviewSessionStatus.OTP_PENDING: {
        InterviewSessionStatus.ACTIVE,
        InterviewSessionStatus.EXPIRED,
        InterviewSessionStatus.CANCELLED,
    },
    InterviewSessionStatus.ACTIVE: {
        InterviewSessionStatus.COMPLETED,
        InterviewSessionStatus.EXPIRED,
        InterviewSessionStatus.CANCELLED,
    },
    InterviewSessionStatus.COMPLETED: set(),
    InterviewSessionStatus.EXPIRED: set(),
    InterviewSessionStatus.CANCELLED: set(),
}


def transition_status(entity: object, field_name: str, target: StatusT, allowed: dict[StatusT, set[StatusT]]) -> None:
    current = getattr(entity, field_name)
    if current == target:
        return
    if target not in allowed.get(current, set()):
        raise ConflictError(f"Invalid {field_name} transition: {current.value} -> {target.value}.")
    setattr(entity, field_name, target)


def transition_job(job: object, target: JobStatus) -> None:
    transition_status(job, "status", target, ALLOWED_JOB_TRANSITIONS)


def transition_candidate(candidate: object, target: CandidateStatus) -> None:
    transition_status(candidate, "status", target, ALLOWED_CANDIDATE_TRANSITIONS)


def transition_interview(interview: object, target: InterviewSessionStatus) -> None:
    transition_status(interview, "status", target, ALLOWED_INTERVIEW_TRANSITIONS)
