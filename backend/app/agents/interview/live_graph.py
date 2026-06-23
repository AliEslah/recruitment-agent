from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from langgraph.graph import END, START, StateGraph

from app.agents.interview.prompts import INTERVIEW_EVALUATION_PROMPT_VERSION, follow_up_prompt
from app.agents.interview.state import LiveInterviewState
from app.agents.shared.utils import append_security_event, is_interview_expired
from app.core.config import get_settings
from app.core.errors import ConflictError
from app.db.models import (
    CandidateStatus,
    InterviewMessage,
    InterviewMessageRole,
    InterviewSessionStatus,
    SecurityEventType,
)
from app.repositories.candidates import CandidateRepository
from app.repositories.interviews import InterviewRepository
from app.schemas.llm_outputs import FollowUpDecisionOutput
from app.services.llm_json import LLMJsonService
from app.services.status_transitions import transition_candidate, transition_interview


async def verify_session_security(state: LiveInterviewState) -> dict:
    interview = await InterviewRepository(state["session"]).get_session(state["interview_session_id"])
    if is_interview_expired(interview):
        transition_interview(interview, InterviewSessionStatus.EXPIRED)
        append_security_event(interview, SecurityEventType.TOKEN_EXPIRED)
        await state["session"].commit()
        raise ConflictError("Interview cannot continue after expiration.")
    if interview.status == InterviewSessionStatus.COMPLETED:
        raise ConflictError("Interview is already completed.")
    if not interview.otp_verified_at:
        raise ConflictError("Candidate cannot start interview before OTP verification.")
    return {"candidate_id": interview.candidate_id, "job_id": interview.job_id, "status": interview.status.value}


async def load_interview_state(state: LiveInterviewState) -> dict:
    interview_repo = InterviewRepository(state["session"])
    interview = await interview_repo.get_session(state["interview_session_id"])
    messages = await interview_repo.messages(interview.id)
    graph_state = interview.graph_state_json or {}
    return {
        "questions": (interview.interview_plan_json or {}).get("questions", []),
        "transcript": [
            {
                "role": message.role.value,
                "content": message.content,
                "question_type": message.question_type,
                "metadata": message.metadata_json or {},
            }
            for message in messages
        ],
        "current_question_index": int(graph_state.get("current_question_index", 0)),
        "follow_up_count": int(graph_state.get("follow_up_count", 0)),
        "max_follow_ups": int(graph_state.get("max_follow_ups", get_settings().max_interview_follow_ups)),
    }


async def record_candidate_answer_if_present(state: LiveInterviewState) -> dict:
    answer = state.get("last_candidate_answer")
    if not answer:
        return {}
    state["session"].add(
        InterviewMessage(
            interview_session_id=state["interview_session_id"],
            role=InterviewMessageRole.CANDIDATE,
            content=answer,
            metadata_json={},
        )
    )
    await state["session"].commit()
    return {
        "transcript": [
            *state.get("transcript", []),
            {"role": InterviewMessageRole.CANDIDATE.value, "content": answer, "question_type": None, "metadata": {}},
        ]
    }


async def decide_next_action(state: LiveInterviewState) -> dict:
    answer = (state.get("last_candidate_answer") or "").strip()
    current_index = state.get("current_question_index", 0)
    has_more_questions = current_index < len(state.get("questions", []))
    needs_follow_up = bool(answer and len(answer.split()) < 6 and state.get("follow_up_count", 0) < state.get("max_follow_ups", 0))
    return {"needs_follow_up": needs_follow_up and has_more_questions}


async def maybe_generate_follow_up(state: LiveInterviewState) -> dict:
    if not state.get("needs_follow_up"):
        return {}
    question_index = max(state.get("current_question_index", 1) - 1, 0)
    question = state.get("questions", [])[question_index]
    output = await LLMJsonService(state["session"]).generate(
        "live_interview.maybe_generate_follow_up",
        follow_up_prompt(question=question, answer=state.get("last_candidate_answer") or ""),
        FollowUpDecisionOutput,
        prompt_version=INTERVIEW_EVALUATION_PROMPT_VERSION,
    )
    if not output.should_ask_follow_up or output.next_action != "ASK_FOLLOW_UP" or not output.follow_up_question:
        return {}
    state["session"].add(
        InterviewMessage(
            interview_session_id=state["interview_session_id"],
            role=InterviewMessageRole.AI,
            content=output.follow_up_question,
            question_type="FOLLOW_UP",
            metadata_json={"reason": output.reason},
        )
    )
    await state["session"].commit()
    return {
        "next_message": output.follow_up_question,
        "follow_up_count": state.get("follow_up_count", 0) + 1,
    }


async def get_next_question(state: LiveInterviewState) -> dict:
    if state.get("next_message"):
        return {}
    index = state.get("current_question_index", 0)
    questions = state.get("questions", [])
    if index >= len(questions):
        return {"completed": True, "next_message": None}
    question = questions[index]
    state["session"].add(
        InterviewMessage(
            interview_session_id=state["interview_session_id"],
            role=InterviewMessageRole.AI,
            content=question["question"],
            question_type=question["type"],
            metadata_json={
                "purpose": question.get("purpose"),
                "evaluation_criteria": question.get("evaluation_criteria"),
                "weight": question.get("weight"),
                "is_mandatory": question.get("is_mandatory"),
            },
        )
    )
    await state["session"].commit()
    return {"current_question_index": index + 1, "next_message": question["question"]}


async def persist_turn_state(state: LiveInterviewState) -> dict:
    interview = await InterviewRepository(state["session"]).get_session(state["interview_session_id"])
    interview.graph_state_json = {
        "current_question_index": state.get("current_question_index", 0),
        "follow_up_count": state.get("follow_up_count", 0),
        "max_follow_ups": state.get("max_follow_ups", get_settings().max_interview_follow_ups),
    }
    if interview.status in {InterviewSessionStatus.OTP_PENDING, InterviewSessionStatus.INVITED, InterviewSessionStatus.DRAFT}:
        transition_interview(interview, InterviewSessionStatus.ACTIVE)
        interview.started_at = interview.started_at or datetime.now(UTC)
    await state["session"].commit()
    return {"status": interview.status.value}


async def complete_if_finished(state: LiveInterviewState) -> dict:
    if not state.get("completed"):
        return {}
    interview = await InterviewRepository(state["session"]).get_session(state["interview_session_id"])
    transition_interview(interview, InterviewSessionStatus.COMPLETED)
    interview.ended_at = datetime.now(UTC)
    append_security_event(interview, SecurityEventType.SESSION_COMPLETED)
    candidate = await CandidateRepository(state["session"]).get(interview.candidate_id)
    transition_candidate(candidate, CandidateStatus.INTERVIEW_COMPLETED)
    await state["session"].commit()
    return {"status": interview.status.value, "completed": True}


def live_route(state: LiveInterviewState) -> Literal["complete_if_finished", "get_next_question"]:
    if state.get("completed"):
        return "complete_if_finished"
    return "get_next_question"


def build_live_interview_graph():
    builder = StateGraph(LiveInterviewState)
    builder.add_node("verify_session_security", verify_session_security)
    builder.add_node("load_interview_state", load_interview_state)
    builder.add_node("record_candidate_answer_if_present", record_candidate_answer_if_present)
    builder.add_node("decide_next_action", decide_next_action)
    builder.add_node("maybe_generate_follow_up", maybe_generate_follow_up)
    builder.add_node("get_next_question", get_next_question)
    builder.add_node("persist_turn_state", persist_turn_state)
    builder.add_node("complete_if_finished", complete_if_finished)
    builder.add_edge(START, "verify_session_security")
    builder.add_edge("verify_session_security", "load_interview_state")
    builder.add_edge("load_interview_state", "record_candidate_answer_if_present")
    builder.add_edge("record_candidate_answer_if_present", "decide_next_action")
    builder.add_edge("decide_next_action", "maybe_generate_follow_up")
    builder.add_conditional_edges("maybe_generate_follow_up", live_route, ["get_next_question", "complete_if_finished"])
    builder.add_edge("get_next_question", "persist_turn_state")
    builder.add_edge("persist_turn_state", "complete_if_finished")
    builder.add_edge("complete_if_finished", END)
    return builder.compile()


async def run_live_interview_graph(state: LiveInterviewState) -> LiveInterviewState:
    graph = build_live_interview_graph()
    return await graph.ainvoke(state)
