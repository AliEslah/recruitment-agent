from __future__ import annotations

from app.evaluation.quality import (
    check_candidate_scoring,
    check_consistency,
    check_criteria_weights,
    check_evidence_grounding,
    check_interview_evaluation,
    check_recommendation_band,
    detect_duplicate_criteria,
    scan_protected_terms,
)


def test_criteria_weight_validation_detects_bad_total() -> None:
    warnings = check_criteria_weights([{"name": "A", "weight": 40}, {"name": "B", "weight": 40}])

    assert warnings[0]["code"] == "criteria_weight_total"


def test_duplicate_criteria_detection() -> None:
    warnings = detect_duplicate_criteria([{"name": "Discovery"}, {"name": "discovery"}])

    assert warnings[0]["code"] == "duplicate_criterion"


def test_recommendation_band_consistency() -> None:
    warnings = check_recommendation_band(85, "WEAK_MATCH")

    assert warnings[0]["code"] == "recommendation_score_mismatch"


def test_evidence_grounding_helper_marks_supported_text() -> None:
    results = check_evidence_grounding(["Maintained Salesforce opportunity notes"], "Maintained Salesforce notes daily.", location="resume")

    assert results[0]["status"] in {"grounded", "weakly_grounded"}


def test_protected_term_scanner_flags_risky_language() -> None:
    warnings = scan_protected_terms("Seeking a digital native for the team.", location="jd")

    assert warnings[0]["code"] == "protected_term"
    assert warnings[0]["category"] == "age"


def test_protected_term_scanner_does_not_flag_technical_single() -> None:
    warnings = scan_protected_terms("Created approval request in a single API call.", location="evidence")

    assert warnings == []


def test_candidate_scoring_grounding_ignores_missing_evidence_concerns() -> None:
    warnings, grounding = check_candidate_scoring(
        {
            "overall_score": 70,
            "criteria_scores": [
                {
                    "criterion_name": "API design",
                    "score": 70,
                    "weight": 100,
                    "evidence": ["Designed REST APIs"],
                    "concerns": ["No explicit database tuning evidence"],
                }
            ],
            "risks": ["Database tuning not validated"],
            "recommendation": "POSSIBLE_MATCH",
            "confidence": 0.7,
        },
        "Designed REST APIs for workflow approvals.",
    )

    assert [item["evidence"] for item in grounding] == ["Designed REST APIs"]
    assert not any(item["code"] == "criteria_score_missing_evidence" for item in warnings)


def test_interview_evaluation_grounding_checks_evidence_fields_separately() -> None:
    _, grounding = check_interview_evaluation(
        {
            "evidence": {
                "communication": "I acknowledge the impact first and confirm reproduction steps.",
                "tooling": "Used Zendesk macros in prior support workflow.",
            },
            "red_flags": [],
            "missing_evidence": ["Tooling was not validated in transcript"],
        },
        "CANDIDATE: I acknowledge the impact first and confirm reproduction steps.",
    )

    assert len(grounding) == 2
    assert grounding[0]["location"] == "interview_evaluation.evidence.communication"
    assert grounding[0]["status"] == "grounded"
    assert grounding[1]["location"] == "interview_evaluation.evidence.tooling"
    assert grounding[1]["status"] == "unsupported"


def test_consistency_check_flags_score_divergence() -> None:
    warnings = check_consistency(
        profile={"skills": ["Salesforce"]},
        transcript_text="Candidate discussed discovery but did not mention Salesforce.",
        candidate_score={"overall_score": 88, "risks": ["No negotiation example"]},
        interview_evaluation={"overall_score": 55},
        final_scorecard={"recommendation": "Recommend human review for discovery evidence."},
    )

    codes = {warning["code"] for warning in warnings}
    assert "score_divergence" in codes
    assert "missing_risk_in_final" in codes
