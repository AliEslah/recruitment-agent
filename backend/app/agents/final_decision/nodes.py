from __future__ import annotations

from sqlalchemy import select

from app.agents.final_decision.prompts import FINAL_SCORECARD_PROMPT_VERSION, final_scorecard_prompt
from app.agents.final_decision.state import FinalDecisionState
from app.core.errors import ConflictError, ValidationAppError
from app.db.models import CandidateScore, FinalScorecard, InterviewEvaluation
from app.schemas.llm_outputs import FinalScorecardOutput
from app.services.llm_json import LLMJsonService


async def load_full_candidate_context(state: FinalDecisionState) -> dict:
    candidate_score = await state["session"].scalar(
        select(CandidateScore)
        .where(CandidateScore.candidate_id == state["candidate_id"], CandidateScore.job_id == state["job_id"])
        .order_by(CandidateScore.created_at.desc())
        .limit(1)
    )
    interview_evaluation = await state["session"].scalar(
        select(InterviewEvaluation)
        .where(
            InterviewEvaluation.candidate_id == state["candidate_id"],
            InterviewEvaluation.job_id == state["job_id"],
        )
        .order_by(InterviewEvaluation.created_at.desc())
        .limit(1)
    )
    if not candidate_score or not interview_evaluation:
        raise ConflictError("Candidate score and interview evaluation are required before final scorecard.")
    return {
        "candidate_score": {
            "overall_score": candidate_score.overall_score,
            "criteria_scores": candidate_score.criteria_scores_json,
            "strengths": candidate_score.strengths_json,
            "weaknesses": candidate_score.weaknesses_json,
            "risks": candidate_score.risks_json,
            "recommendation": candidate_score.recommendation,
            "confidence": candidate_score.confidence,
        },
        "interview_evaluation": {
            "overall_score": interview_evaluation.overall_score,
            "competency_scores": interview_evaluation.competency_scores_json,
            "soft_skill_scores": interview_evaluation.soft_skill_scores_json,
            "strengths": interview_evaluation.strengths_json,
            "weaknesses": interview_evaluation.weaknesses_json,
            "red_flags": interview_evaluation.red_flags_json,
            "evidence": interview_evaluation.evidence_json,
            "missing_evidence": interview_evaluation.missing_evidence_json,
            "recommendation": interview_evaluation.recommendation,
            "confidence": interview_evaluation.confidence,
        },
    }


async def generate_final_scorecard(state: FinalDecisionState) -> dict:
    output = await LLMJsonService(state["session"]).generate(
        "final_decision.generate_final_scorecard",
        final_scorecard_prompt(
            candidate_score=state["candidate_score"],
            interview_evaluation=state["interview_evaluation"],
        ),
        FinalScorecardOutput,
        prompt_version=FINAL_SCORECARD_PROMPT_VERSION,
    )
    return {"final_scorecard": output.model_dump(mode="json")}


async def validate_final_scorecard(state: FinalDecisionState) -> dict:
    if "overall_fit" not in state.get("final_scorecard", {}):
        raise ValidationAppError("Final scorecard must include overall_fit.")
    return {}


async def persist_final_scorecard(state: FinalDecisionState) -> dict:
    scorecard = state["final_scorecard"]
    state["session"].add(
        FinalScorecard(
            candidate_id=state["candidate_id"],
            job_id=state["job_id"],
            resume_score=scorecard["resume_score"],
            interview_score=scorecard["interview_score"],
            soft_skill_score=scorecard["soft_skill_score"],
            overall_fit=scorecard["overall_fit"],
            risk_level=scorecard["risk_level"],
            evidence_summary_json=scorecard["evidence_summary"],
            candidate_fit_narrative=scorecard["candidate_fit_narrative"],
            missing_evidence_json=scorecard.get("missing_evidence", []),
            recommendation=scorecard["recommendation"],
            confidence=scorecard["confidence"],
        )
    )
    await state["session"].commit()
    return {}
