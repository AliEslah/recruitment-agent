from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROLE_REQUIRED_FIELDS = {
    "title",
    "department",
    "seniority",
    "location",
    "employment_type",
    "raw_jd",
    "expected_must_haves",
    "expected_nice_to_haves",
    "expected_soft_skills",
    "expected_disqualifiers",
    "expected_knockout_areas",
    "scoring_notes",
}

CANDIDATE_REQUIRED_FIELDS = {
    "candidate_id",
    "name",
    "resume_text",
    "expected_strengths",
    "expected_risks",
    "expected_missing_evidence",
    "expected_recommendation_band",
    "human_notes",
}

TRANSCRIPT_REQUIRED_FIELDS = {
    "candidate_id",
    "job_id",
    "messages",
    "expected_soft_skill_notes",
    "expected_red_flags",
    "expected_missing_evidence",
    "expected_interview_recommendation_band",
    "human_notes",
}


@dataclass(frozen=True)
class RoleFixtureSet:
    role_id: str
    family: str
    role: dict[str, Any]
    candidates: list[dict[str, Any]]
    transcripts: list[dict[str, Any]]
    expected: dict[str, Any]


def default_evals_root() -> Path:
    return Path(__file__).resolve().parents[3] / "evals"


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return data


def _missing_fields(data: dict[str, Any], required: set[str]) -> set[str]:
    return {field for field in required if field not in data}


def validate_role_fixture(path: Path, data: dict[str, Any]) -> None:
    missing = _missing_fields(data, ROLE_REQUIRED_FIELDS)
    if missing:
        raise ValueError(f"{path} is missing role fields: {', '.join(sorted(missing))}")


def validate_candidate_fixture(path: Path, data: dict[str, Any]) -> None:
    missing = _missing_fields(data, CANDIDATE_REQUIRED_FIELDS)
    if missing:
        raise ValueError(f"{path} is missing candidate fields: {', '.join(sorted(missing))}")


def validate_transcript_fixture(path: Path, data: dict[str, Any]) -> None:
    missing = _missing_fields(data, TRANSCRIPT_REQUIRED_FIELDS)
    if missing:
        raise ValueError(f"{path} is missing transcript fields: {', '.join(sorted(missing))}")
    messages = data.get("messages")
    if not isinstance(messages, list) or not messages:
        raise ValueError(f"{path} must include at least one transcript message.")


def load_eval_fixtures(root: Path | None = None, *, role: str | None = None) -> list[RoleFixtureSet]:
    evals_root = root or default_evals_root()
    fixtures_root = evals_root / "fixtures"
    roles_root = fixtures_root / "roles"
    role_paths = sorted(roles_root.glob("*.json"))
    if role:
        role_path = roles_root / f"{role}.json"
        if not role_path.exists():
            raise ValueError(f"No role fixture found for '{role}' at {role_path}.")
        role_paths = [role_path]

    fixture_sets: list[RoleFixtureSet] = []
    for role_path in role_paths:
        role_id = role_path.stem
        role_data = read_json(role_path)
        validate_role_fixture(role_path, role_data)
        family = str(role_data.get("family") or role_id.split("_")[0])

        candidate_paths = sorted((fixtures_root / "resumes" / family).glob("*.json"))
        candidates = []
        for candidate_path in candidate_paths:
            candidate = read_json(candidate_path)
            validate_candidate_fixture(candidate_path, candidate)
            if candidate.get("job_id") == role_id:
                candidates.append(candidate)

        transcript_paths = sorted((fixtures_root / "transcripts" / family).glob("*.json"))
        transcripts = []
        for transcript_path in transcript_paths:
            transcript = read_json(transcript_path)
            validate_transcript_fixture(transcript_path, transcript)
            if transcript.get("job_id") == role_id:
                transcripts.append(transcript)

        expected_path = fixtures_root / "expected" / f"{role_id}.expected.json"
        expected = read_json(expected_path) if expected_path.exists() else {}
        fixture_sets.append(
            RoleFixtureSet(
                role_id=role_id,
                family=family,
                role=role_data,
                candidates=candidates,
                transcripts=transcripts,
                expected=expected,
            )
        )
    return fixture_sets
