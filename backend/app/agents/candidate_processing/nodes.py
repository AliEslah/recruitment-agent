from __future__ import annotations

import re

from app.agents.candidate_processing.prompts import parse_resume_prompt, score_candidate_prompt
from app.agents.candidate_processing.state import CandidateProcessingState
from app.core.errors import ConflictError, ValidationAppError
from app.db.models import CandidateScore, CandidateStatus, JobStatus
from app.repositories.candidates import CandidateRepository
from app.repositories.jobs import JobRepository
from app.schemas.llm_outputs import CandidateScoreOutput, ParsedResumeOutput
from app.services.llm_json import LLMJsonService
from app.services.pdf_parser import extract_text_from_file
from app.services.status_transitions import transition_candidate

LINK_RE = re.compile(r"https?://[^\s)>\"]+|(?:linkedin\.com|github\.com|portfolio\.)[^\s)>\"]+", re.IGNORECASE)


async def load_candidate_and_job(state: CandidateProcessingState) -> dict:
    candidate = await CandidateRepository(state["session"]).get(state["candidate_id"])
    job = await JobRepository(state["session"]).get(state["job_id"])
    if candidate.job_id != job.id:
        raise ValidationAppError("Candidate does not belong to the requested job.")
    if job.status != JobStatus.APPROVED:
        raise ConflictError("Candidate scoring requires an APPROVED job.")
    if not candidate.resume_file_path:
        raise ValidationAppError("Candidate has no uploaded resume.")
    if (
        not state.get("force")
        and candidate.resume_hash
        and candidate.parsed_profile_json
        and candidate.enriched_profile_json
    ):
        existing_score = await CandidateRepository(state["session"]).latest_score(candidate.id, job.id)
        if existing_score:
            return {
                "resume_text": candidate.resume_text or "",
                "resume_hash": candidate.resume_hash,
                "parsed_profile": candidate.parsed_profile_json,
                "enriched_profile": candidate.enriched_profile_json,
                "job_criteria": job.criteria_json or [],
                "candidate_score": {
                    "overall_score": existing_score.overall_score,
                    "criteria_scores": existing_score.criteria_scores_json,
                    "strengths": existing_score.strengths_json,
                    "weaknesses": existing_score.weaknesses_json,
                    "risks": existing_score.risks_json,
                    "recommendation": existing_score.recommendation,
                    "confidence": existing_score.confidence,
                },
                "skip_processing": True,
            }
    return {
        "resume_hash": candidate.resume_hash,
        "job_criteria": job.criteria_json or [],
        "must_haves": job.must_haves_json or [],
        "disqualifiers": job.disqualifiers_json or [],
    }


async def extract_resume_text(state: CandidateProcessingState) -> dict:
    candidate = await CandidateRepository(state["session"]).get(state["candidate_id"])
    if state.get("resume_text"):
        return {}
    return {"resume_text": extract_text_from_file(candidate.resume_file_path or "")}


async def parse_resume(state: CandidateProcessingState) -> dict:
    if state.get("parsed_profile"):
        return {}
    output = await LLMJsonService(state["session"]).generate(
        "candidate_processing.parse_resume",
        parse_resume_prompt(state["resume_text"]),
        ParsedResumeOutput,
    )
    return {"parsed_profile": output.model_dump(mode="json")}


async def extract_links(state: CandidateProcessingState) -> dict:
    links = set(state.get("parsed_profile", {}).get("links") or [])
    links.update(match.group(0) for match in LINK_RE.finditer(state.get("resume_text", "")))
    return {"extracted_links": sorted(links)}


async def build_enriched_profile(state: CandidateProcessingState) -> dict:
    profile = dict(state["parsed_profile"])
    profile["links"] = state.get("extracted_links", [])
    return {"enriched_profile": profile}


async def score_candidate(state: CandidateProcessingState) -> dict:
    if state.get("candidate_score"):
        return {}
    output = await LLMJsonService(state["session"]).generate(
        "candidate_processing.score_candidate",
        score_candidate_prompt(
            profile=state["enriched_profile"],
            criteria=state.get("job_criteria", []),
            must_haves=state.get("must_haves", []),
            disqualifiers=state.get("disqualifiers", []),
        ),
        CandidateScoreOutput,
    )
    return {"candidate_score": output.model_dump(mode="json")}


async def apply_basic_rules(state: CandidateProcessingState) -> dict:
    score = dict(state["candidate_score"])
    if score.get("overall_score", 0) < 50 and score.get("recommendation") == "POSSIBLE_MATCH":
        score["recommendation"] = "NEEDS_REVIEW"
    return {"candidate_score": score}


async def persist_candidate_results(state: CandidateProcessingState) -> dict:
    if state.get("skip_processing"):
        return {}
    candidate_repo = CandidateRepository(state["session"])
    candidate = await candidate_repo.get(state["candidate_id"])
    candidate.resume_text = state["resume_text"]
    candidate.parsed_profile_json = state["parsed_profile"]
    candidate.enriched_profile_json = state["enriched_profile"]
    candidate.name = candidate.name or state["parsed_profile"].get("name")
    candidate.email = candidate.email or state["parsed_profile"].get("email")
    candidate.phone = candidate.phone or state["parsed_profile"].get("phone")
    next_status = CandidateStatus.NEEDS_REVIEW if state["candidate_score"]["recommendation"] == "NEEDS_REVIEW" else CandidateStatus.SCORED
    transition_candidate(candidate, next_status)

    score = state["candidate_score"]
    state["session"].add(
        CandidateScore(
            candidate_id=state["candidate_id"],
            job_id=state["job_id"],
            overall_score=score["overall_score"],
            criteria_scores_json=score["criteria_scores"],
            strengths_json=score.get("strengths", []),
            weaknesses_json=score.get("weaknesses", []),
            risks_json=score.get("risks", []),
            evidence_json={"criteria_scores": score["criteria_scores"]},
            recommendation=score["recommendation"],
            confidence=score["confidence"],
        )
    )
    await state["session"].commit()
    return {}
