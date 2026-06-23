from __future__ import annotations

from app.agents.shared.prompts import GENERAL_SCORING_RULES


def final_scorecard_prompt(*, candidate_score: dict, interview_evaluation: dict) -> str:
    return (
        "Create a final evidence-based candidate scorecard for human review. "
        "Do not make the final hiring decision. Keep narrative under 120 words and lists to at most 3 items.\n"
        f"Resume score: {candidate_score}\nInterview evaluation: {interview_evaluation}\n\n{GENERAL_SCORING_RULES}"
    )
