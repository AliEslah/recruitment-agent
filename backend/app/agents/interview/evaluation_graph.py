from __future__ import annotations

from langgraph.graph import END, START, StateGraph
from sqlalchemy import select

from app.agents.interview.prompts import INTERVIEW_EVALUATION_PROMPT_VERSION, interview_evaluation_prompt
from app.agents.interview.state import InterviewEvaluationState
from app.core.errors import ConflictError, ValidationAppError
from app.db.models import CandidateScore, InterviewEvaluation, InterviewSessionStatus
from app.repositories.candidates import CandidateRepository
from app.repositories.interviews import InterviewRepository
from app.repositories.jobs import JobRepository
from app.schemas.llm_outputs import InterviewEvaluationOutput
from app.services.llm_json import LLMJsonService


async def load_completed_interview(state: InterviewEvaluationState) -> dict:
    interview_repo = InterviewRepository(state["session"])
    interview = await interview_repo.get_session(state["interview_session_id"])
    if interview.status != InterviewSessionStatus.COMPLETED:
        raise ConflictError("Only COMPLETED interviews can be evaluated.")
    candidate = await CandidateRepository(state["session"]).get(interview.candidate_id)
    job = await JobRepository(state["session"]).get(interview.job_id)
    score = await state["session"].scalar(
        select(CandidateScore)
        .where(CandidateScore.candidate_id == candidate.id, CandidateScore.job_id == job.id)
        .order_by(CandidateScore.created_at.desc())
        .limit(1)
    )
    if not score:
        raise ConflictError("Resume score is required before interview evaluation.")
    messages = await interview_repo.messages(interview.id)
    return {
        "candidate_id": candidate.id,
        "job_id": job.id,
        "transcript": [
            {"role": message.role.value, "content": message.content, "question_type": message.question_type}
            for message in messages
        ],
        "job_criteria": job.criteria_json or [],
        "candidate_profile": candidate.enriched_profile_json or candidate.parsed_profile_json or {},
        "resume_score": {
            "overall_score": score.overall_score,
            "criteria_scores": score.criteria_scores_json,
            "recommendation": score.recommendation,
            "confidence": score.confidence,
        },
    }


async def validate_transcript(state: InterviewEvaluationState) -> dict:
    transcript = state.get("transcript", [])
    if not any(message.get("role") == "CANDIDATE" for message in transcript):
        raise ValidationAppError("Interview transcript must include candidate answers.")
    return {}


async def evaluate_interview(state: InterviewEvaluationState) -> dict:
    output = await LLMJsonService(state["session"]).generate(
        "interview_evaluation.evaluate_interview",
        interview_evaluation_prompt(
            transcript=state["transcript"],
            criteria=state["job_criteria"],
            profile=state["candidate_profile"],
            resume_score=state["resume_score"],
        ),
        InterviewEvaluationOutput,
        prompt_version=INTERVIEW_EVALUATION_PROMPT_VERSION,
    )
    return {"interview_evaluation": output.model_dump(mode="json")}


async def check_resume_interview_consistency(state: InterviewEvaluationState) -> dict:
    return {}


async def validate_evaluation(state: InterviewEvaluationState) -> dict:
    if "overall_score" not in state.get("interview_evaluation", {}):
        raise ValidationAppError("Interview evaluation must include an overall score.")
    return {}


async def persist_evaluation(state: InterviewEvaluationState) -> dict:
    evaluation = state["interview_evaluation"]
    state["session"].add(
        InterviewEvaluation(
            interview_session_id=state["interview_session_id"],
            candidate_id=state["candidate_id"],
            job_id=state["job_id"],
            overall_score=evaluation["overall_score"],
            competency_scores_json=evaluation["competency_scores"],
            soft_skill_scores_json=evaluation["soft_skill_scores"],
            strengths_json=evaluation.get("strengths", []),
            weaknesses_json=evaluation.get("weaknesses", []),
            red_flags_json=evaluation.get("red_flags", []),
            evidence_json=evaluation.get("evidence", []),
            missing_evidence_json=evaluation.get("missing_evidence", []),
            recommendation=evaluation.get("recommendation", "NEEDS_REVIEW"),
            confidence=evaluation.get("confidence", 0),
        )
    )
    await state["session"].commit()
    return {}


def build_interview_evaluation_graph():
    builder = StateGraph(InterviewEvaluationState)
    builder.add_node("load_completed_interview", load_completed_interview)
    builder.add_node("validate_transcript", validate_transcript)
    builder.add_node("evaluate_interview", evaluate_interview)
    builder.add_node("check_resume_interview_consistency", check_resume_interview_consistency)
    builder.add_node("validate_evaluation", validate_evaluation)
    builder.add_node("persist_evaluation", persist_evaluation)
    builder.add_edge(START, "load_completed_interview")
    builder.add_edge("load_completed_interview", "validate_transcript")
    builder.add_edge("validate_transcript", "evaluate_interview")
    builder.add_edge("evaluate_interview", "check_resume_interview_consistency")
    builder.add_edge("check_resume_interview_consistency", "validate_evaluation")
    builder.add_edge("validate_evaluation", "persist_evaluation")
    builder.add_edge("persist_evaluation", END)
    return builder.compile()


async def run_interview_evaluation_graph(state: InterviewEvaluationState) -> InterviewEvaluationState:
    graph = build_interview_evaluation_graph()
    return await graph.ainvoke(state)
