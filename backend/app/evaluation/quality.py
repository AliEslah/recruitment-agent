from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any, Literal

WarningSeverity = Literal["info", "warning", "error"]
GroundingStatus = Literal["grounded", "weakly_grounded", "unsupported"]

RECOMMENDATION_BANDS = {"STRONG_MATCH", "POSSIBLE_MATCH", "WEAK_MATCH", "NEEDS_REVIEW"}

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "candidate",
    "for",
    "from",
    "has",
    "have",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "role",
    "that",
    "the",
    "this",
    "to",
    "with",
}

PROTECTED_TERM_PATTERNS: dict[str, list[str]] = {
    "age": [
        r"\bage\b",
        r"\baged\b",
        r"\byoung\b",
        r"\byounger\b",
        r"\bold(er)?\b",
        r"\bover\s+40\b",
        r"\brecent\s+graduate\b",
        r"\bdigital\s+native\b",
    ],
    "gender": [
        r"\bgender\b",
        r"\bmale\b",
        r"\bfemale\b",
        r"\bman\b",
        r"\bwoman\b",
        r"\bmother\b",
        r"\bfather\b",
    ],
    "marital_or_family_status": [
        r"\bmarital\b",
        r"\bmarried\b",
        r"\bsingle\s+(parent|mother|father|status)\b",
        r"\bdivorced\b",
        r"\bchildcare\b",
        r"\bfamily\s+status\b",
        r"\bpregnan(cy|t)\b",
    ],
    "religion": [
        r"\breligion\b",
        r"\bchristian\b",
        r"\bmuslim\b",
        r"\bjewish\b",
        r"\bhindu\b",
        r"\bchurch\b",
        r"\bmosque\b",
        r"\bsynagogue\b",
    ],
    "race_or_ethnicity": [
        r"\brace\b",
        r"\bethnicity\b",
        r"\bethnic\b",
        r"\bblack\b",
        r"\bwhite\b",
        r"\basian\b",
        r"\blatino\b",
        r"\bhispanic\b",
    ],
    "nationality": [
        r"\bnationality\b",
        r"\bnative\s+english\b",
        r"\bcitizen(ship)?\b",
        r"\bvisa\b",
        r"\bforeign\b",
    ],
    "disability": [
        r"\bdisab(ility|led)\b",
        r"\bable[-\s]?bodied\b",
        r"\bhealthy\b",
        r"\bmedical\s+condition\b",
    ],
    "political_affiliation": [
        r"\bpolitical\b",
        r"\bparty\s+affiliation\b",
        r"\bunion\b",
    ],
}


def make_warning(code: str, message: str, *, severity: WarningSeverity = "warning", location: str | None = None) -> dict[str, str]:
    warning = {"code": code, "severity": severity, "message": message}
    if location:
        warning["location"] = location
    return warning


def flatten_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        return " ".join(flatten_text(item) for item in value.values())
    if isinstance(value, Iterable) and not isinstance(value, (bytes, bytearray)):
        return " ".join(flatten_text(item) for item in value)
    return str(value)


def tokenize(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9][a-z0-9+#.\-']*", text.lower())
        if len(token) > 2 and token not in STOPWORDS
    }


def evidence_items(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, Mapping):
        preferred = []
        for key in ("evidence", "evidence_summary", "concerns", "red_flags", "strengths", "weaknesses", "risks"):
            if key in value:
                preferred.extend(evidence_items(value[key]))
        if preferred:
            return preferred
        return [flatten_text(value)] if flatten_text(value).strip() else []
    if isinstance(value, Iterable) and not isinstance(value, (bytes, bytearray)):
        items: list[str] = []
        for item in value:
            items.extend(evidence_items(item))
        return items
    text = str(value)
    return [text] if text.strip() else []


def grounding_status(evidence: str, source_text: str) -> tuple[GroundingStatus, float]:
    evidence_tokens = tokenize(evidence)
    if not evidence_tokens:
        return "unsupported", 0.0
    source_tokens = tokenize(source_text)
    if not source_tokens:
        return "unsupported", 0.0
    overlap = len(evidence_tokens.intersection(source_tokens)) / len(evidence_tokens)
    if overlap >= 0.5:
        return "grounded", round(overlap, 3)
    if overlap >= 0.25:
        return "weakly_grounded", round(overlap, 3)
    return "unsupported", round(overlap, 3)


def check_evidence_grounding(evidence: Any, source_text: str, *, location: str) -> list[dict[str, Any]]:
    results = []
    for item in evidence_items(evidence):
        status, overlap = grounding_status(item, source_text)
        results.append({"location": location, "evidence": item, "status": status, "token_overlap": overlap})
    return results


def check_mapping_value_grounding(
    value: Any,
    source_text: str,
    *,
    location: str,
) -> list[dict[str, Any]]:
    if not isinstance(value, Mapping):
        return check_evidence_grounding(value, source_text, location=location)
    results: list[dict[str, Any]] = []
    for key, item in value.items():
        child_location = f"{location}.{key}"
        results.extend(check_evidence_grounding(item, source_text, location=child_location))
    return results


def scan_protected_terms(value: Any, *, location: str) -> list[dict[str, str]]:
    text = flatten_text(value).lower()
    warnings: list[dict[str, str]] = []
    for category, patterns in PROTECTED_TERM_PATTERNS.items():
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                warnings.append(
                    make_warning(
                        "protected_term",
                        f"Potential protected-attribute term '{match.group(0)}' found.",
                        location=location,
                    )
                    | {"category": category}
                )
                break
    return warnings


def criteria_weight_total(criteria: list[dict[str, Any]]) -> float:
    return round(sum(float(item.get("weight") or 0) for item in criteria), 2)


def check_criteria_weights(criteria: list[dict[str, Any]], *, location: str = "criteria") -> list[dict[str, str]]:
    if not criteria:
        return [make_warning("criteria_empty", "No criteria were produced.", severity="error", location=location)]
    total = criteria_weight_total(criteria)
    if total != 100:
        return [
            make_warning(
                "criteria_weight_total",
                f"Criteria weights sum to {total}, expected 100.",
                severity="error",
                location=location,
            )
        ]
    return []


def detect_duplicate_criteria(criteria: list[dict[str, Any]], *, location: str = "criteria") -> list[dict[str, str]]:
    seen: set[str] = set()
    warnings: list[dict[str, str]] = []
    for item in criteria:
        name = str(item.get("name") or item.get("criterion_name") or "").strip().lower()
        if not name:
            continue
        if name in seen:
            warnings.append(
                make_warning("duplicate_criterion", f"Duplicate criterion '{name}' found.", location=location)
            )
        seen.add(name)
    return warnings


def expected_recommendation_band(overall_score: float) -> str:
    if overall_score >= 80:
        return "STRONG_MATCH"
    if overall_score >= 60:
        return "POSSIBLE_MATCH"
    if overall_score >= 40:
        return "WEAK_MATCH"
    return "NEEDS_REVIEW"


def check_recommendation_band(
    overall_score: float | int | None,
    recommendation: str | None,
    *,
    location: str = "recommendation",
) -> list[dict[str, str]]:
    if recommendation not in RECOMMENDATION_BANDS:
        return [
            make_warning(
                "invalid_recommendation_band",
                f"Recommendation '{recommendation}' is not an allowed band.",
                severity="error",
                location=location,
            )
        ]
    if overall_score is None:
        return [make_warning("missing_score", "Overall score is missing.", severity="error", location=location)]
    expected = expected_recommendation_band(float(overall_score))
    if recommendation != expected:
        return [
            make_warning(
                "recommendation_score_mismatch",
                f"Recommendation '{recommendation}' does not match score-based band '{expected}'.",
                location=location,
            )
        ]
    return []


def check_expected_recommendation_band(
    output: dict[str, Any],
    expected: dict[str, Any],
    *,
    location: str = "recommendation",
) -> list[dict[str, str]]:
    expected_band = expected.get("expected_recommendation_band")
    actual_band = output.get("recommendation")
    if not expected_band or not actual_band:
        return []
    if actual_band != expected_band:
        return [
            make_warning(
                "expected_recommendation_band_mismatch",
                f"Recommendation '{actual_band}' differs from fixture expected band '{expected_band}'.",
                location=location,
            )
        ]
    return []


def check_job_calibration(output: dict[str, Any]) -> list[dict[str, str]]:
    warnings: list[dict[str, str]] = []
    criteria = output.get("criteria") or []
    warnings.extend(check_criteria_weights(criteria))
    warnings.extend(detect_duplicate_criteria(criteria))
    if not output.get("must_haves"):
        warnings.append(make_warning("must_haves_empty", "Must-haves are empty.", location="must_haves"))
    if not output.get("knockout_areas"):
        warnings.append(make_warning("knockout_areas_empty", "Knockout areas are empty.", location="knockout_areas"))
    warnings.extend(scan_protected_terms(output.get("improved_jd"), location="improved_jd"))
    warnings.extend(scan_protected_terms(criteria, location="criteria"))
    warnings.extend(scan_protected_terms(output.get("disqualifiers"), location="disqualifiers"))
    return warnings


def check_resume_parsing(parsed_profile: dict[str, Any], resume_text: str) -> list[dict[str, str]]:
    warnings: list[dict[str, str]] = []
    email = parsed_profile.get("email")
    if email and not re.search(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", str(email)):
        warnings.append(make_warning("implausible_email", "Parsed email is not plausible.", location="email"))
    years = parsed_profile.get("years_of_experience")
    if years is not None and not isinstance(years, int | float):
        warnings.append(
            make_warning("invalid_years_of_experience", "Years of experience must be numeric or null.", location="years")
        )
    resume_lower = resume_text.lower()
    for link in parsed_profile.get("links") or []:
        if str(link).lower() not in resume_lower:
            warnings.append(make_warning("invented_link", f"Parsed link '{link}' is not present.", location="links"))
    warnings.extend(
        unsupported_profile_claims(
            parsed_profile,
            resume_text,
            keys=("skills", "certifications", "projects", "achievements", "summary"),
        )
    )
    return warnings


def unsupported_profile_claims(
    profile: dict[str, Any],
    source_text: str,
    *,
    keys: tuple[str, ...],
) -> list[dict[str, str]]:
    warnings: list[dict[str, str]] = []
    for key in keys:
        for result in check_evidence_grounding(profile.get(key), source_text, location=key):
            if result["status"] == "unsupported":
                warnings.append(
                    make_warning(
                        "unsupported_profile_claim",
                        f"Parsed {key} item has low source overlap: {result['evidence']}",
                        location=key,
                    )
                )
    return warnings


def check_candidate_scoring(score: dict[str, Any], source_text: str) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    warnings: list[dict[str, str]] = []
    criteria_scores = score.get("criteria_scores") or []
    for index, item in enumerate(criteria_scores):
        evidence = item.get("evidence") or []
        concerns = item.get("concerns") or []
        if not evidence and not concerns:
            warnings.append(
                make_warning(
                    "criteria_score_missing_evidence",
                    "Criterion score has no evidence or missing-evidence concern.",
                    severity="error",
                    location=f"criteria_scores[{index}]",
                )
            )
    evidence_for_grounding = [item.get("evidence") or [] for item in criteria_scores]
    grounding = check_evidence_grounding(
        evidence_for_grounding,
        source_text,
        location="candidate_score.criteria_scores",
    )
    warnings.extend(
        check_recommendation_band(score.get("overall_score"), score.get("recommendation"), location="candidate_score")
    )
    warnings.extend(scan_protected_terms(score, location="candidate_score"))
    if not score.get("risks"):
        warnings.append(make_warning("risks_empty", "Risk list is empty.", location="candidate_score.risks"))
    return warnings, grounding


def check_interview_plan(plan: dict[str, Any]) -> list[dict[str, str]]:
    warnings: list[dict[str, str]] = []
    questions = plan.get("questions") or []
    types = {item.get("type") for item in questions}
    for required in {"FIXED", "RESUME_VALIDATION", "SOFT_SKILL", "KNOCKOUT"}:
        if required not in types:
            warnings.append(make_warning("missing_question_type", f"Missing {required} question.", location="questions"))
    if not any(item.get("is_mandatory") for item in questions):
        warnings.append(make_warning("missing_mandatory_question", "No mandatory question found.", location="questions"))
    texts = [str(item.get("question") or "").strip().lower() for item in questions]
    if len(texts) != len(set(texts)):
        warnings.append(make_warning("duplicate_question", "Interview plan has duplicate questions.", location="questions"))
    warnings.extend(scan_protected_terms(questions, location="interview_plan.questions"))
    return warnings


def check_interview_evaluation(
    evaluation: dict[str, Any],
    transcript_text: str,
) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    warnings: list[dict[str, str]] = []
    evidence = evaluation.get("evidence") or []
    if not evidence:
        warnings.append(make_warning("interview_evidence_empty", "Interview evidence is empty.", severity="error"))
    if not evaluation.get("missing_evidence"):
        warnings.append(make_warning("interview_missing_evidence_empty", "Missing evidence list is empty."))
    grounding = check_mapping_value_grounding(evidence, transcript_text, location="interview_evaluation.evidence")
    grounding.extend(
        check_evidence_grounding(evaluation.get("red_flags"), transcript_text, location="interview_evaluation.red_flags")
    )
    warnings.extend(scan_protected_terms(evaluation, location="interview_evaluation"))
    return warnings, grounding


def check_final_scorecard(scorecard: dict[str, Any]) -> list[dict[str, str]]:
    warnings: list[dict[str, str]] = []
    for key in ("resume_score", "interview_score", "risk_level", "evidence_summary", "missing_evidence", "recommendation"):
        if scorecard.get(key) in (None, "", []):
            warnings.append(make_warning("final_scorecard_missing_field", f"Missing {key}.", location=key))
    recommendation = str(scorecard.get("recommendation") or "").lower()
    if re.search(r"\bhire\b|\bhired\b|\bdo not hire\b", recommendation):
        warnings.append(
            make_warning(
                "final_decision_language",
                "Recommendation appears to make a final hiring decision.",
                severity="error",
                location="recommendation",
            )
        )
    warnings.extend(scan_protected_terms(scorecard, location="final_scorecard"))
    return warnings


def score_value(value: Any) -> float | None:
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, Mapping):
        for key in ("overall_score", "overall_fit", "score"):
            if isinstance(value.get(key), int | float):
                return float(value[key])
    return None


def check_consistency(
    *,
    profile: dict[str, Any],
    transcript_text: str,
    candidate_score: dict[str, Any] | None = None,
    interview_evaluation: dict[str, Any] | None = None,
    final_scorecard: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    warnings: list[dict[str, str]] = []
    transcript_tokens = tokenize(transcript_text)
    for skill in profile.get("skills") or []:
        skill_tokens = tokenize(str(skill))
        if skill_tokens and not skill_tokens.intersection(transcript_tokens):
            warnings.append(
                make_warning(
                    "needs_validation",
                    f"Resume skill '{skill}' was not validated in transcript.",
                    location="profile.skills",
                )
            )
    if candidate_score and interview_evaluation:
        resume_score = score_value(candidate_score)
        interview_score = score_value(interview_evaluation)
        if resume_score is not None and interview_score is not None and abs(resume_score - interview_score) >= 25:
            warnings.append(
                make_warning(
                    "score_divergence",
                    f"Resume score {resume_score} and interview score {interview_score} diverge by at least 25 points.",
                )
            )
    if candidate_score and final_scorecard:
        risks = [str(item).lower() for item in candidate_score.get("risks") or []]
        final_text = flatten_text(final_scorecard).lower()
        for risk in risks:
            risk_tokens = tokenize(risk)
            if risk_tokens and not risk_tokens.intersection(tokenize(final_text)):
                warnings.append(
                    make_warning(
                        "missing_risk_in_final",
                        f"Final scorecard may ignore candidate-score risk: {risk}",
                        location="final_scorecard",
                    )
                )
    profile_tokens = tokenize(flatten_text(profile))
    for token in transcript_tokens:
        if token in STOPWORDS or len(token) < 4:
            continue
        if token not in profile_tokens and token in {"salesforce", "zendesk", "excel", "ga4", "python", "sql"}:
            warnings.append(
                make_warning(
                    "new_positive_signal",
                    f"Transcript mentions '{token}' not clearly present in resume profile.",
                    severity="info",
                    location="transcript",
                )
            )
    return warnings
