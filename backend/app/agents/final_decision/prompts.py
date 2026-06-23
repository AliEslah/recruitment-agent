from __future__ import annotations

from app.agents.shared.prompts import GENERAL_SCORING_RULES

FINAL_SCORECARD_PROMPT_VERSION = "final-scorecard-v2"


def final_scorecard_prompt(*, candidate_score: dict, interview_evaluation: dict) -> str:
    return (
        f"Prompt version: {FINAL_SCORECARD_PROMPT_VERSION}\n"
        "Create a final evidence-based candidate scorecard for human review. "
        "Summarize resume score, interview score, main hiring risks, missing validation areas, and fit narrative. "
        "Do not say hire as a final decision. Use next-step language such as recommend human review, "
        "move to next round, or hold for additional validation. Keep narrative under 120 words and lists to at most 3 items.\n"
        f"Resume score: {candidate_score}\nInterview evaluation: {interview_evaluation}\n\n{GENERAL_SCORING_RULES}"
    )
