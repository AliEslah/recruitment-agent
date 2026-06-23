from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.interview.evaluation_graph import run_interview_evaluation_graph
from app.agents.interview.live_graph import run_live_interview_graph
from app.agents.interview.planning_graph import run_interview_planning_graph
from app.agents.shared.utils import append_security_event, is_interview_expired
from app.api.deps import require_recruiter_user
from app.core.config import get_settings
from app.core.errors import ConflictError, ValidationAppError
from app.db.models import AuditLog, CandidateStatus, InterviewSessionStatus, PilotFeedback, SecurityEventType, User
from app.db.session import get_session
from app.repositories.candidates import CandidateRepository
from app.repositories.feedback import FeedbackRepository
from app.repositories.interviews import InterviewRepository
from app.repositories.jobs import JobRepository
from app.repositories.logs import LogRepository
from app.schemas.feedback import CandidateInterviewFeedbackCreate, PilotFeedbackType
from app.schemas.common import MessageResponse
from app.schemas.interviews import (
    CandidateAnswerRequest,
    CompleteInterviewRequest,
    InterviewEntryRead,
    InterviewEvaluationRead,
    InterviewInviteResponse,
    InterviewMessageRead,
    InterviewPlanUpdate,
    InterviewSessionRead,
    InterviewSessionSummaryRead,
    LiveInterviewTurnResponse,
    VerifyOtpRequest,
)
from app.services.email import EmailService
from app.services.otp import generate_otp, hash_otp, verify_otp
from app.services.redaction import SecretRedaction
from app.services.tokens import generate_token, hash_token
from app.services.status_transitions import transition_candidate, transition_interview

router = APIRouter(tags=["interviews"], dependencies=[Depends(require_recruiter_user)])
entry_router = APIRouter(tags=["interviews"])


def _interview_summary_read(interview, latest_evaluation) -> InterviewSessionSummaryRead:
    questions = (interview.interview_plan_json or {}).get("questions", [])
    return InterviewSessionSummaryRead(
        id=interview.id,
        job_id=interview.job_id,
        candidate_id=interview.candidate_id,
        mode=interview.mode,
        status=interview.status,
        expires_at=interview.expires_at,
        started_at=interview.started_at,
        ended_at=interview.ended_at,
        created_at=interview.created_at,
        question_count=len(questions) if isinstance(questions, list) else 0,
        evaluation_status="EVALUATED" if latest_evaluation else "NOT_EVALUATED",
    )


@router.post("/candidates/{candidate_id}/interview-plan", response_model=InterviewSessionRead)
async def create_interview_plan(candidate_id: UUID, session: AsyncSession = Depends(get_session)) -> InterviewSessionRead:
    candidate = await CandidateRepository(session).get(candidate_id)
    result = await run_interview_planning_graph({"session": session, "candidate_id": candidate.id, "job_id": candidate.job_id})
    return await InterviewRepository(session).get_session(result["interview_session_id"])


@router.get("/interviews/{session_id}", response_model=InterviewSessionRead)
async def get_interview(session_id: UUID, session: AsyncSession = Depends(get_session)) -> InterviewSessionRead:
    return await InterviewRepository(session).get_session(session_id)


@router.get("/candidates/{candidate_id}/interviews", response_model=list[InterviewSessionSummaryRead])
async def list_candidate_interviews(
    candidate_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> list[InterviewSessionSummaryRead]:
    await CandidateRepository(session).get(candidate_id)
    interview_repo = InterviewRepository(session)
    interviews = await interview_repo.list_for_candidate(candidate_id)
    evaluations = await interview_repo.latest_evaluations_for_sessions([interview.id for interview in interviews])
    return [_interview_summary_read(interview, evaluations.get(interview.id)) for interview in interviews]


@router.get("/jobs/{job_id}/interviews", response_model=list[InterviewSessionSummaryRead])
async def list_job_interviews(job_id: UUID, session: AsyncSession = Depends(get_session)) -> list[InterviewSessionSummaryRead]:
    await JobRepository(session).get(job_id)
    interview_repo = InterviewRepository(session)
    interviews = await interview_repo.list_for_job(job_id)
    evaluations = await interview_repo.latest_evaluations_for_sessions([interview.id for interview in interviews])
    return [_interview_summary_read(interview, evaluations.get(interview.id)) for interview in interviews]


@router.get("/interviews/{session_id}/plan")
async def get_interview_plan(session_id: UUID, session: AsyncSession = Depends(get_session)) -> dict:
    interview = await InterviewRepository(session).get_session(session_id)
    return interview.interview_plan_json or {}


@router.patch("/interviews/{session_id}/plan", response_model=InterviewSessionRead)
async def update_interview_plan(
    session_id: UUID,
    payload: InterviewPlanUpdate,
    session: AsyncSession = Depends(get_session),
) -> InterviewSessionRead:
    interview = await InterviewRepository(session).get_session(session_id)
    interview.interview_plan_json = payload.interview_plan_json
    await session.commit()
    await session.refresh(interview)
    return interview


@router.post("/interviews/{session_id}/send-invite", response_model=InterviewInviteResponse)
async def send_invite(
    session_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_recruiter_user),
) -> InterviewInviteResponse:
    settings = get_settings()
    interview = await InterviewRepository(session).get_session(session_id)
    candidate = await CandidateRepository(session).get(interview.candidate_id)
    if not candidate.email:
        raise ValidationAppError("Candidate email is required to send an interview invite.")
    raw_token = generate_token()
    interview.secure_token_hash = hash_token(raw_token)
    interview.client_session_hash = None
    interview.expires_at = datetime.now(UTC) + timedelta(hours=settings.interview_token_ttl_hours)
    transition_interview(interview, InterviewSessionStatus.INVITED)
    transition_candidate(candidate, CandidateStatus.INTERVIEW_INVITED)
    await session.commit()
    link = settings.candidate_interview_url(raw_token)
    await EmailService(session).send(
        to_email=candidate.email,
        subject="Your interview invitation",
        body=f"Open this secure interview link once you are ready: {link}\nThis link expires at {interview.expires_at}.",
        job_id=interview.job_id,
        candidate_id=candidate.id,
        interview_session_id=interview.id,
        template="interview_invitation",
        secrets_to_redact=[SecretRedaction(raw_token, "[REDACTED_INTERVIEW_TOKEN]")],
    )
    await LogRepository(session).audit(
        AuditLog(
            actor_user_id=current_user.id,
            entity_type="interview_session",
            entity_id=interview.id,
            action="SEND_INTERVIEW_INVITE",
            metadata_json={"candidate_id": str(candidate.id)},
        )
    )
    return InterviewInviteResponse(message="Interview invite sent.", expires_at=interview.expires_at)


@router.get("/interviews/{session_id}/transcript", response_model=list[InterviewMessageRead])
async def get_transcript(session_id: UUID, session: AsyncSession = Depends(get_session)) -> list[InterviewMessageRead]:
    return await InterviewRepository(session).messages(session_id)


@router.post("/interviews/{session_id}/evaluate", response_model=InterviewEvaluationRead)
async def evaluate_interview(
    session_id: UUID,
    force: bool = False,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_recruiter_user),
) -> InterviewEvaluationRead:
    existing = await InterviewRepository(session).latest_evaluation(session_id)
    if existing and not force:
        return existing
    await run_interview_evaluation_graph({"session": session, "interview_session_id": session_id})
    evaluation = await InterviewRepository(session).latest_evaluation(session_id)
    if not evaluation:
        raise ConflictError("Interview evaluation was not created.")
    await LogRepository(session).audit(
        AuditLog(
            actor_user_id=current_user.id,
            entity_type="interview_session",
            entity_id=session_id,
            action="EVALUATE_INTERVIEW",
            metadata_json={"evaluation_id": str(evaluation.id), "force": force},
        )
    )
    return evaluation


@router.get("/interviews/{session_id}/evaluation", response_model=InterviewEvaluationRead)
async def get_evaluation(session_id: UUID, session: AsyncSession = Depends(get_session)) -> InterviewEvaluationRead:
    evaluation = await InterviewRepository(session).latest_evaluation(session_id)
    if not evaluation:
        raise ConflictError("Interview evaluation has not been created.")
    return evaluation


async def _entry_session(token: str, session: AsyncSession, *, allow_completed: bool = False) -> tuple:
    interview = await InterviewRepository(session).get_by_token_hash(hash_token(token))
    if interview.status == InterviewSessionStatus.COMPLETED and not allow_completed:
        raise ConflictError("Interview cannot continue after completion.")
    if is_interview_expired(interview):
        transition_interview(interview, InterviewSessionStatus.EXPIRED)
        append_security_event(interview, SecurityEventType.TOKEN_EXPIRED)
        await session.commit()
        raise ConflictError("Interview cannot continue after expiration.")
    return interview, await CandidateRepository(session).get(interview.candidate_id)


@entry_router.get("/interview-entry/{token}", response_model=InterviewEntryRead)
async def interview_entry(token: str, session: AsyncSession = Depends(get_session)) -> InterviewEntryRead:
    interview, _ = await _entry_session(token, session, allow_completed=True)
    if interview.status != InterviewSessionStatus.COMPLETED:
        append_security_event(interview, SecurityEventType.TOKEN_OPENED)
        await session.commit()
    return InterviewEntryRead(
        session_id=interview.id,
        candidate_id=interview.candidate_id,
        job_id=interview.job_id,
        status=interview.status,
        expires_at=interview.expires_at,
        otp_verified=bool(interview.otp_verified_at),
    )


@entry_router.post("/interview-entry/{token}/send-otp", response_model=MessageResponse)
async def send_otp(token: str, session: AsyncSession = Depends(get_session)) -> MessageResponse:
    settings = get_settings()
    interview, candidate = await _entry_session(token, session)
    if not candidate.email:
        raise ValidationAppError("Candidate email is required to send OTP.")
    otp = generate_otp()
    interview.otp_hash = hash_otp(otp)
    interview.otp_expires_at = datetime.now(UTC) + timedelta(minutes=settings.otp_ttl_minutes)
    transition_interview(interview, InterviewSessionStatus.OTP_PENDING)
    append_security_event(interview, SecurityEventType.OTP_SENT)
    await session.commit()
    await EmailService(session).send(
        to_email=candidate.email,
        subject="Your interview OTP",
        body=f"Your interview OTP is {otp}. It expires in {settings.otp_ttl_minutes} minutes.",
        job_id=interview.job_id,
        candidate_id=candidate.id,
        interview_session_id=interview.id,
        template="otp",
        secrets_to_redact=[SecretRedaction(otp, "[REDACTED_OTP]")],
    )
    return MessageResponse(message="OTP sent.")


@entry_router.post("/interview-entry/{token}/verify-otp", response_model=MessageResponse)
async def verify_entry_otp(
    token: str,
    payload: VerifyOtpRequest,
    session: AsyncSession = Depends(get_session),
) -> MessageResponse:
    interview, _ = await _entry_session(token, session)
    otp_expires_at = interview.otp_expires_at
    if otp_expires_at and otp_expires_at.tzinfo is None:
        otp_expires_at = otp_expires_at.replace(tzinfo=UTC)
    if not otp_expires_at or otp_expires_at <= datetime.now(UTC):
        append_security_event(interview, SecurityEventType.INVALID_OTP, {"reason": "expired"})
        await session.commit()
        raise ConflictError("OTP expired.")
    if not verify_otp(payload.otp, interview.otp_hash):
        append_security_event(interview, SecurityEventType.INVALID_OTP)
        await session.commit()
        raise ConflictError("Invalid OTP.")
    interview.otp_verified_at = datetime.now(UTC)
    append_security_event(interview, SecurityEventType.OTP_VERIFIED)
    await session.commit()
    return MessageResponse(message="OTP verified.")


@entry_router.post("/interview-entry/{token}/start", response_model=LiveInterviewTurnResponse)
async def start_interview(token: str, session: AsyncSession = Depends(get_session)) -> LiveInterviewTurnResponse:
    interview, candidate = await _entry_session(token, session)
    if not interview.otp_verified_at:
        raise ConflictError("Candidate cannot start interview before OTP verification.")
    if interview.status == InterviewSessionStatus.ACTIVE and interview.single_session_lock:
        append_security_event(interview, SecurityEventType.MULTIPLE_SESSION_ATTEMPT)
        await session.commit()
        raise ConflictError("Interview already has one active session.")
    interview.single_session_lock = interview.single_session_lock or generate_token()
    client_session_nonce = generate_token()
    interview.client_session_hash = hash_token(client_session_nonce)
    append_security_event(interview, SecurityEventType.SESSION_STARTED)
    transition_candidate(candidate, CandidateStatus.INTERVIEW_ACTIVE)
    await session.commit()
    result = await run_live_interview_graph({"session": session, "interview_session_id": interview.id})
    return LiveInterviewTurnResponse(
        status=InterviewSessionStatus(result["status"]),
        current_question_index=result.get("current_question_index", 0),
        message=result.get("next_message"),
        completed=result.get("completed", False),
        client_session_nonce=client_session_nonce,
    )


def _verify_client_session_nonce(interview, nonce: str | None) -> None:
    if not nonce or not interview.client_session_hash or hash_token(nonce) != interview.client_session_hash:
        append_security_event(interview, SecurityEventType.MULTIPLE_SESSION_ATTEMPT)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid interview client session.")


@entry_router.post("/interview-entry/{token}/answer", response_model=LiveInterviewTurnResponse)
async def answer_interview(
    token: str,
    payload: CandidateAnswerRequest,
    session: AsyncSession = Depends(get_session),
) -> LiveInterviewTurnResponse:
    interview, _ = await _entry_session(token, session)
    try:
        _verify_client_session_nonce(interview, payload.client_session_nonce)
    except HTTPException:
        await session.commit()
        raise
    result = await run_live_interview_graph(
        {"session": session, "interview_session_id": interview.id, "last_candidate_answer": payload.answer}
    )
    return LiveInterviewTurnResponse(
        status=InterviewSessionStatus(result["status"]),
        current_question_index=result.get("current_question_index", 0),
        message=result.get("next_message"),
        completed=result.get("completed", False),
    )


@entry_router.post("/interview-entry/{token}/complete", response_model=MessageResponse)
async def complete_interview(
    token: str,
    payload: CompleteInterviewRequest | None = None,
    session: AsyncSession = Depends(get_session),
) -> MessageResponse:
    interview, candidate = await _entry_session(token, session, allow_completed=True)
    if interview.status == InterviewSessionStatus.COMPLETED:
        return MessageResponse(message="Interview completed.")
    try:
        _verify_client_session_nonce(interview, payload.client_session_nonce if payload else None)
    except HTTPException:
        await session.commit()
        raise
    graph_state = interview.graph_state_json or {}
    questions = (interview.interview_plan_json or {}).get("questions", [])
    if int(graph_state.get("current_question_index", 0)) < len(questions):
        raise ConflictError("Required interview questions are not finished.")
    transition_interview(interview, InterviewSessionStatus.COMPLETED)
    interview.ended_at = datetime.now(UTC)
    transition_candidate(candidate, CandidateStatus.INTERVIEW_COMPLETED)
    append_security_event(interview, SecurityEventType.SESSION_COMPLETED)
    await session.commit()
    if candidate.email:
        await EmailService(session).send(
            to_email=candidate.email,
            subject="Interview completed",
            body="Your chat interview has been completed. Thank you.",
            job_id=interview.job_id,
            candidate_id=candidate.id,
            interview_session_id=interview.id,
            template="interview_completed",
        )
    return MessageResponse(message="Interview completed.")


@entry_router.post("/interview-entry/{token}/feedback", response_model=MessageResponse)
async def candidate_interview_feedback(
    token: str,
    payload: CandidateInterviewFeedbackCreate,
    session: AsyncSession = Depends(get_session),
) -> MessageResponse:
    interview = await InterviewRepository(session).get_by_token_hash(hash_token(token))
    if interview.status != InterviewSessionStatus.COMPLETED:
        raise ConflictError("Feedback can be submitted after interview completion.")
    feedback = PilotFeedback(
        user_id=None,
        candidate_id=interview.candidate_id,
        job_id=interview.job_id,
        interview_session_id=interview.id,
        feedback_type=PilotFeedbackType.CANDIDATE_INTERVIEW_FEEDBACK.value,
        rating=payload.rating,
        comment=payload.comment,
        metadata_json={"source": "candidate_interview_completion"},
    )
    await FeedbackRepository(session).create(feedback)
    return MessageResponse(message="Feedback submitted.")
