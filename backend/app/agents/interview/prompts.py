from __future__ import annotations

from app.agents.shared.prompts import GENERAL_SCORING_RULES

INTERVIEW_PLANNING_PROMPT_VERSION = "interview-planning-v2"
INTERVIEW_EVALUATION_PROMPT_VERSION = "interview-evaluation-v7"


def interview_plan_prompt(*, criteria: list[dict], profile: dict, score: dict) -> str:
    return (
        f"Prompt version: {INTERVIEW_PLANNING_PROMPT_VERSION}\n"
        "Create a chat interview plan for this shortlisted candidate. "
        "Include fixed, resume-validation, soft-skill, knockout, and optional dynamic questions. "
        "Questions must validate job criteria, resume claims, risks, and missing evidence. "
        "Do not ask illegal or protected-attribute questions. Avoid repetitive wording. "
        "Return exactly 5 questions. Every mandatory and knockout area must be covered. "
        "Keep each question under 30 words.\n"
        f"Criteria: {criteria}\nCandidate profile: {profile}\nResume score: {score}\n\n{GENERAL_SCORING_RULES}"
    )


def follow_up_prompt(*, question: dict, answer: str) -> str:
    return (
        f"Prompt version: {INTERVIEW_EVALUATION_PROMPT_VERSION}\n"
        "Decide whether a short follow-up question is needed for this answer. "
        "Only ask if the answer lacks evidence for the evaluation criteria. "
        "Do not probe protected attributes. Keep reason under 20 words.\n"
        f"Question: {question}\nAnswer: {answer}\n\n{GENERAL_SCORING_RULES}"
    )


def interview_evaluation_prompt(*, transcript: list[dict], criteria: list[dict], profile: dict, resume_score: dict) -> str:
    return (
        f"Prompt version: {INTERVIEW_EVALUATION_PROMPT_VERSION}\n"
        "Evaluate this completed chat interview using only transcript evidence and job criteria. "
        "Candidate profile and resume score are context only; do not cite them as interview evidence. "
        "Use evidence as a list of 2-4 short items that quote or directly summarize candidate answers from the transcript only. "
        "Do not create criterion-named evidence entries for criteria that were not discussed. "
        "Do not mention resume-only facts, tools, volumes, CSAT, employers, or prior workflow claims in evidence unless the candidate said them in the transcript. "
        "Do not write missing-evidence statements such as 'does not mention' inside evidence. "
        "Move unvalidated criteria, resume-only tools, volumes, employers, and prior workflow claims to missing_evidence. "
        "Keep behavioral interpretation separate from the transcript fact it rests on. "
        "If the transcript does not validate a resume claim, put that gap in missing_evidence instead of evidence. "
        "Every major score, soft-skill score, red flag, and risk must cite or summarize specific transcript evidence. "
        "Red flags must be negative behaviors or contradictions observed in the transcript; do not use red_flags for mere missing evidence. "
        "Do not over-interpret short answers. Do not infer personality from protected attributes. "
        "Compare resume claims with interview answers and surface missing validation explicitly. "
        "Include soft skill scores from communication content, missing evidence, and confidence. "
        "Keep all lists to at most 3 items.\n"
        f"Transcript: {transcript}\nCriteria: {criteria}\nCandidate profile: {profile}\nResume score: {resume_score}\n\n"
        f"{GENERAL_SCORING_RULES}"
    )
