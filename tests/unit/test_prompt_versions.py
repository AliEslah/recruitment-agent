from __future__ import annotations

from app.agents.candidate_processing.prompts import CANDIDATE_SCORING_PROMPT_VERSION, RESUME_PARSING_PROMPT_VERSION
from app.agents.final_decision.prompts import FINAL_SCORECARD_PROMPT_VERSION
from app.agents.interview.prompts import INTERVIEW_EVALUATION_PROMPT_VERSION, INTERVIEW_PLANNING_PROMPT_VERSION
from app.agents.job_calibration.prompts import JOB_CALIBRATION_PROMPT_VERSION


def test_prompt_version_constants_exist() -> None:
    versions = {
        JOB_CALIBRATION_PROMPT_VERSION,
        RESUME_PARSING_PROMPT_VERSION,
        CANDIDATE_SCORING_PROMPT_VERSION,
        INTERVIEW_PLANNING_PROMPT_VERSION,
        INTERVIEW_EVALUATION_PROMPT_VERSION,
        FINAL_SCORECARD_PROMPT_VERSION,
    }

    assert versions == {
        "job-calibration-v2",
        "resume-parsing-v3",
        "candidate-scoring-v6",
        "interview-planning-v2",
        "interview-evaluation-v7",
        "final-scorecard-v2",
    }
