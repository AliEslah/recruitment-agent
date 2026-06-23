from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


def none_to_empty_list(value):
    return [] if value is None else value


class JDImprovementOutput(BaseModel):
    improved_jd: str
    missing_info: list[str] = Field(default_factory=list)
    suggested_clarifying_questions: list[str] = Field(default_factory=list)

    _none_to_empty_lists = field_validator("missing_info", "suggested_clarifying_questions", mode="before")(
        none_to_empty_list
    )


class HiringCriterion(BaseModel):
    name: str
    description: str
    weight: float
    evidence_guidance: str


class HiringRubricOutput(BaseModel):
    criteria: list[HiringCriterion]
    must_haves: list[str] = Field(default_factory=list)
    nice_to_haves: list[str] = Field(default_factory=list)
    disqualifiers: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    knockout_areas: list[str] = Field(default_factory=list)

    _none_to_empty_lists = field_validator(
        "must_haves",
        "nice_to_haves",
        "disqualifiers",
        "soft_skills",
        "knockout_areas",
        mode="before",
    )(none_to_empty_list)


class WorkExperienceItem(BaseModel):
    company: str | None = None
    title: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    responsibilities: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)

    _none_to_empty_lists = field_validator("responsibilities", "achievements", mode="before")(none_to_empty_list)


class EducationItem(BaseModel):
    institution: str | None = None
    degree: str | None = None
    field: str | None = None
    year: str | None = None


class ParsedResumeOutput(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    years_of_experience: float | None = None
    seniority: str | None = None
    skills: list[str] = Field(default_factory=list)
    work_experience: list[WorkExperienceItem] = Field(default_factory=list)
    education: list[EducationItem] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)
    summary: str | None = None

    _none_to_empty_lists = field_validator(
        "skills",
        "work_experience",
        "education",
        "certifications",
        "projects",
        "achievements",
        "links",
        mode="before",
    )(none_to_empty_list)


class CandidateCriterionScore(BaseModel):
    criterion_name: str
    score: float
    weight: float
    evidence: list[str] = Field(default_factory=list)
    concerns: list[str] = Field(default_factory=list)

    _none_to_empty_lists = field_validator("evidence", "concerns", mode="before")(none_to_empty_list)


class CandidateScoreOutput(BaseModel):
    overall_score: float
    criteria_scores: list[CandidateCriterionScore]
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    recommendation: Literal["STRONG_MATCH", "POSSIBLE_MATCH", "WEAK_MATCH", "NEEDS_REVIEW"]
    confidence: float

    _none_to_empty_lists = field_validator(
        "criteria_scores",
        "strengths",
        "weaknesses",
        "risks",
        mode="before",
    )(none_to_empty_list)


QuestionType = Literal["FIXED", "RESUME_VALIDATION", "SOFT_SKILL", "KNOCKOUT", "DYNAMIC", "FOLLOW_UP"]


class InterviewQuestion(BaseModel):
    type: QuestionType
    question: str
    purpose: str
    evaluation_criteria: str
    weight: float
    is_mandatory: bool


class InterviewPlanOutput(BaseModel):
    questions: list[InterviewQuestion]

    _none_to_empty_lists = field_validator("questions", mode="before")(none_to_empty_list)


class FollowUpDecisionOutput(BaseModel):
    should_ask_follow_up: bool
    follow_up_question: str | None = None
    reason: str
    next_action: Literal["ASK_FOLLOW_UP", "MOVE_NEXT", "COMPLETE"]


class InterviewEvaluationOutput(BaseModel):
    overall_score: float
    competency_scores: list[dict] | dict
    soft_skill_scores: list[dict] | dict
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
    evidence: list[dict] | dict
    missing_evidence: list[str] = Field(default_factory=list)
    recommendation: str = Field(max_length=2000)
    confidence: float

    _none_to_empty_lists = field_validator(
        "strengths",
        "weaknesses",
        "red_flags",
        "missing_evidence",
        mode="before",
    )(none_to_empty_list)


class FinalScorecardOutput(BaseModel):
    overall_fit: float
    resume_score: float
    interview_score: float
    soft_skill_score: float
    risk_level: str
    evidence_summary: list[dict] | dict
    candidate_fit_narrative: str
    missing_evidence: list[str] = Field(default_factory=list)
    recommendation: str = Field(max_length=2000)
    confidence: float

    _none_to_empty_lists = field_validator("missing_evidence", mode="before")(none_to_empty_list)
