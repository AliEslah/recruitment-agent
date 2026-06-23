from __future__ import annotations

from app.agents.shared.prompts import GENERAL_SCORING_RULES

CANDIDATE_SCORING_PROMPT_VERSION = "candidate-scoring-v6"
RESUME_PARSING_PROMPT_VERSION = "resume-parsing-v3"


def parse_resume_prompt(resume_text: str) -> str:
    return (
        f"Prompt version: {RESUME_PARSING_PROMPT_VERSION}\n"
        "Parse this resume into structured candidate profile JSON. Extract only facts present in the resume. "
        "Do not infer companies, degrees, dates, tools, links, or years of experience. "
        "Use null only for absent scalar fields. Use [] for absent list fields. "
        "Keep the summary under 80 words and exclude unsupported claims. "
        "Return at most 5 skills, 3 work_experience items, 2 education items, 3 projects, 3 achievements, and 3 links.\n"
        f"Resume:\n{resume_text}\n\n{GENERAL_SCORING_RULES}"
    )


def score_candidate_prompt(
    *,
    profile: dict,
    criteria: list[dict],
    must_haves: list[str],
    disqualifiers: list[str],
) -> str:
    return (
        f"Prompt version: {CANDIDATE_SCORING_PROMPT_VERSION}\n"
        "Score this candidate against the approved job criteria only. Use 0-100 scores. "
        "Return one criteria_scores item per criterion. Every criterion score must include resume evidence or a concern "
        "that states the missing evidence. Overall score must align with weighted criteria. "
        "Each evidence string must quote or directly summarize facts stated in the candidate profile/resume. "
        "Do not put inferred traits, implied case studies, likely buyer type, tone, or unstated outcomes in evidence. "
        "Do not use standalone trait phrases like calm, empathetic, proactive, strong, proven, or under pressure as evidence; cite the resume fact instead. "
        "If support is indirect, put the inference or gap in concerns/risks instead of evidence. "
        "Do not give 90+ criterion scores when evidence lacks outcomes, depth, or required validation. "
        "Material missing evidence should lower the criterion score and appear in risks. "
        "Consider must-haves and disqualifiers; triggered disqualifiers should reduce the recommendation. "
        "Use STRONG_MATCH only when most must-haves have strong direct evidence and there are no material gaps. "
        "Use POSSIBLE_MATCH for relevant candidates with important validation gaps. "
        "Do not return STRONG_MATCH when risks include material missing evidence or validation gaps. "
        "recommendation must be one of STRONG_MATCH, POSSIBLE_MATCH, WEAK_MATCH, NEEDS_REVIEW. "
        "Limit strengths, weaknesses, and risks to at most 3 each.\n"
        f"Approved criteria: {criteria}\nMust haves: {must_haves}\nDisqualifiers: {disqualifiers}\n"
        f"Candidate profile: {profile}\n\n{GENERAL_SCORING_RULES}"
    )
