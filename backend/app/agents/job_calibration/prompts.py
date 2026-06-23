from __future__ import annotations

from app.agents.shared.prompts import GENERAL_SCORING_RULES

JOB_CALIBRATION_PROMPT_VERSION = "job-calibration-v2"


def jd_improvement_prompt(*, title: str, raw_jd: str, department: str | None, seniority: str | None) -> str:
    return (
        f"Prompt version: {JOB_CALIBRATION_PROMPT_VERSION}\n"
        "Improve this raw job description for recruiting calibration. Keep it factual, concise, and role-specific. "
        "Remove vague hype and discriminatory or protected-attribute language. "
        "Do not add requirements that are not supported by the raw JD; put gaps in missing_info. "
        "Limit improved_jd to 180 words and missing_info to at most 5 items.\n"
        f"Title: {title}\nDepartment: {department or 'unknown'}\nSeniority: {seniority or 'unknown'}\n"
        f"Raw JD:\n{raw_jd}\n\n{GENERAL_SCORING_RULES}"
    )


def rubric_prompt(*, title: str, improved_jd: str, location: str | None, employment_type: str | None) -> str:
    return (
        f"Prompt version: {JOB_CALIBRATION_PROMPT_VERSION}\n"
        "Extract a weighted hiring rubric from this job description. "
        "Return exactly 4 criteria. Criteria weights must sum to 100 before normalization. "
        "Each criterion must be observable from resume or interview evidence. "
        "Must-haves, disqualifiers, and knockout areas must be job-related and non-discriminatory. "
        "Keep every description and evidence_guidance under 25 words. Limit each string list to at most 5 items.\n"
        f"Title: {title}\nLocation: {location or 'unknown'}\nEmployment type: {employment_type or 'unknown'}\n"
        f"Improved JD:\n{improved_jd}\n\n{GENERAL_SCORING_RULES}"
    )
