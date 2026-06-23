from __future__ import annotations

from langgraph.graph import END, START, StateGraph
from sqlalchemy import select

from app.agents.interview.prompts import interview_plan_prompt
from app.agents.interview.state import InterviewPlanningState
from app.core.errors import ConflictError, ValidationAppError
from app.db.models import CandidateStatus, InterviewMode, InterviewSession
from app.repositories.candidates import CandidateRepository
from app.repositories.jobs import JobRepository
from app.schemas.llm_outputs import InterviewPlanOutput
from app.services.llm_json import LLMJsonService
from app.db.models import CandidateScore


async def load_context(state: InterviewPlanningState) -> dict:
    candidate = await CandidateRepository(state["session"]).get(state["candidate_id"])
    if candidate.status != CandidateStatus.SHORTLISTED:
        raise ConflictError("Candidate must be SHORTLISTED before interview planning.")
    job = await JobRepository(state["session"]).get(state["job_id"])
    if candidate.job_id != job.id:
        raise ValidationAppError("Candidate does not belong to the requested job.")
    score = await state["session"].scalar(
        select(CandidateScore)
        .where(CandidateScore.candidate_id == candidate.id, CandidateScore.job_id == job.id)
        .order_by(CandidateScore.created_at.desc())
        .limit(1)
    )
    if not score:
        raise ConflictError("Candidate must be scored before interview planning.")
    return {
        "job_criteria": job.criteria_json or [],
        "candidate_profile": candidate.enriched_profile_json or candidate.parsed_profile_json or {},
        "candidate_score": {
            "overall_score": score.overall_score,
            "criteria_scores": score.criteria_scores_json,
            "strengths": score.strengths_json,
            "weaknesses": score.weaknesses_json,
            "risks": score.risks_json,
            "recommendation": score.recommendation,
            "confidence": score.confidence,
        },
    }


async def generate_interview_plan(state: InterviewPlanningState) -> dict:
    output = await LLMJsonService(state["session"]).generate(
        "interview_planning.generate_interview_plan",
        interview_plan_prompt(
            criteria=state["job_criteria"],
            profile=state["candidate_profile"],
            score=state["candidate_score"],
        ),
        InterviewPlanOutput,
    )
    return {"interview_plan": output.model_dump(mode="json")}


async def validate_interview_plan(state: InterviewPlanningState) -> dict:
    questions = state.get("interview_plan", {}).get("questions", [])
    if not questions:
        raise ValidationAppError("Interview plan must include at least one question.")
    if not any(item.get("type") == "KNOCKOUT" for item in questions):
        raise ValidationAppError("Interview plan must include knockout questions.")
    if not any(item.get("is_mandatory") for item in questions):
        raise ValidationAppError("Interview plan must include mandatory questions.")
    return {}


async def persist_interview_plan(state: InterviewPlanningState) -> dict:
    return {}


async def create_interview_session(state: InterviewPlanningState) -> dict:
    interview = InterviewSession(
        job_id=state["job_id"],
        candidate_id=state["candidate_id"],
        mode=InterviewMode.CHAT,
        interview_plan_json=state["interview_plan"],
        graph_state_json={"current_question_index": 0, "follow_up_count": 0},
        security_events_json=[],
    )
    state["session"].add(interview)
    await state["session"].commit()
    await state["session"].refresh(interview)
    return {"interview_session_id": interview.id}


def build_interview_planning_graph():
    builder = StateGraph(InterviewPlanningState)
    builder.add_node("load_context", load_context)
    builder.add_node("generate_interview_plan", generate_interview_plan)
    builder.add_node("validate_interview_plan", validate_interview_plan)
    builder.add_node("persist_interview_plan", persist_interview_plan)
    builder.add_node("create_interview_session", create_interview_session)
    builder.add_edge(START, "load_context")
    builder.add_edge("load_context", "generate_interview_plan")
    builder.add_edge("generate_interview_plan", "validate_interview_plan")
    builder.add_edge("validate_interview_plan", "persist_interview_plan")
    builder.add_edge("persist_interview_plan", "create_interview_session")
    builder.add_edge("create_interview_session", END)
    return builder.compile()


async def run_interview_planning_graph(state: InterviewPlanningState) -> InterviewPlanningState:
    graph = build_interview_planning_graph()
    return await graph.ainvoke(state)

