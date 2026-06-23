from __future__ import annotations

from app.schemas.llm_outputs import ParsedResumeOutput


def test_parsed_resume_null_lists_are_treated_as_absent() -> None:
    parsed = ParsedResumeOutput.model_validate(
        {
            "name": "Synthetic Candidate",
            "email": "candidate@example.test",
            "education": None,
            "certifications": None,
            "projects": None,
            "links": None,
        }
    )

    assert parsed.education == []
    assert parsed.certifications == []
    assert parsed.projects == []
    assert parsed.links == []
