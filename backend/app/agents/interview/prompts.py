from __future__ import annotations

from app.agents.shared.prompts import GENERAL_SCORING_RULES


def interview_plan_prompt(*, criteria: list[dict], profile: dict, score: dict) -> str:
    return (
        "Create a chat interview plan for this shortlisted candidate. "
        "Include fixed, resume validation, soft skill, knockout, and optional dynamic questions. "
        "Return exactly 5 questions. Every mandatory and knockout area must be covered. "
        "Keep each question under 30 words.\n"
        f"Criteria: {criteria}\nCandidate profile: {profile}\nResume score: {score}\n\n{GENERAL_SCORING_RULES}"
    )


def follow_up_prompt(*, question: dict, answer: str) -> str:
    return (
        "Decide whether a short follow-up question is needed for this answer. "
        "Only ask if the answer lacks evidence for the evaluation criteria. Keep reason under 20 words.\n"
        f"Question: {question}\nAnswer: {answer}\n\n{GENERAL_SCORING_RULES}"
    )


def interview_evaluation_prompt(*, transcript: list[dict], criteria: list[dict], profile: dict, resume_score: dict) -> str:
    return (
        "Evaluate this completed chat interview using only transcript evidence and job criteria. "
        "Include soft skill scores from text, missing evidence, and confidence. Keep all lists to at most 3 items.\n"
        f"Transcript: {transcript}\nCriteria: {criteria}\nCandidate profile: {profile}\nResume score: {resume_score}\n\n"
        f"{GENERAL_SCORING_RULES}"
    )
