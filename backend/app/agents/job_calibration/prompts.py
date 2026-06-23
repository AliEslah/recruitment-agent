from __future__ import annotations

from app.agents.shared.prompts import GENERAL_SCORING_RULES


def jd_improvement_prompt(*, title: str, raw_jd: str, department: str | None, seniority: str | None) -> str:
    return (
        "Improve this raw job description for recruiting calibration. "
        "Keep it factual and concise. Limit improved_jd to 180 words and missing_info to at most 5 items.\n"
        f"Title: {title}\nDepartment: {department or 'unknown'}\nSeniority: {seniority or 'unknown'}\n"
        f"Raw JD:\n{raw_jd}\n\n{GENERAL_SCORING_RULES}"
    )


def rubric_prompt(*, title: str, improved_jd: str, location: str | None, employment_type: str | None) -> str:
    return (
        "Extract a weighted hiring rubric from this job description. "
        "Return exactly 4 criteria. Criteria weights must sum to 100 before normalization. "
        "Keep every description and evidence_guidance under 25 words. Limit each string list to at most 5 items.\n"
        f"Title: {title}\nLocation: {location or 'unknown'}\nEmployment type: {employment_type or 'unknown'}\n"
        f"Improved JD:\n{improved_jd}\n\n{GENERAL_SCORING_RULES}"
    )
