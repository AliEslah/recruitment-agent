from __future__ import annotations

from app.agents.shared.prompts import GENERAL_SCORING_RULES


def parse_resume_prompt(resume_text: str) -> str:
    return (
        "Parse this resume into structured candidate profile JSON. Keep the summary under 80 words. "
        "Return at most 5 skills, 3 work_experience items, 2 education items, 3 projects, and 3 achievements.\n"
        f"Resume:\n{resume_text}\n\n{GENERAL_SCORING_RULES}"
    )


def score_candidate_prompt(*, profile: dict, criteria: list[dict], must_haves: list[str], disqualifiers: list[str]) -> str:
    return (
        "Score this candidate against the approved job criteria. "
        "Use 0-100 scores and cite concise resume evidence. Return one criteria_scores item per criterion. "
        "Limit strengths, weaknesses, and risks to at most 3 each.\n"
        f"Approved criteria: {criteria}\nMust haves: {must_haves}\nDisqualifiers: {disqualifiers}\n"
        f"Candidate profile: {profile}\n\n{GENERAL_SCORING_RULES}"
    )
