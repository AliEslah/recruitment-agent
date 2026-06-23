from __future__ import annotations

import asyncio
import hashlib
import json
import os
from importlib.resources import files
from pathlib import Path
from typing import Any

from sqlalchemy import select

from app.db.models import Candidate, CandidateStatus, Job, JobStatus, QuestionBankItem, UserRole
from app.db.session import AsyncSessionLocal
from app.repositories.users import UserRepository
from app.services.auth import hash_password
from app.services.role_templates import load_role_templates

PILOT_USERS = [
    ("Pilot Admin", "pilot.admin@example.local", UserRole.ADMIN),
    ("Pilot Recruiter", "pilot.recruiter@example.local", UserRole.RECRUITER),
    ("Pilot Hiring Manager", "pilot.manager@example.local", UserRole.HIRING_MANAGER),
]

FORBIDDEN_SEED_AI_OUTPUT_KEYS = {
    "criteria_json",
    "must_haves_json",
    "nice_to_haves_json",
    "disqualifiers_json",
    "soft_skills_json",
    "knockout_areas_json",
    "parsed_profile_json",
    "enriched_profile_json",
    "overall_score",
    "criteria_scores_json",
    "strengths_json",
    "weaknesses_json",
    "risks_json",
    "evidence_json",
    "recommendation",
    "confidence",
    "interview_evaluation",
    "final_scorecard",
    "overall_fit",
}


def _load_json_fixture(name: str) -> list[dict[str, Any]]:
    fixture = files("app.fixtures").joinpath(name)
    return json.loads(fixture.read_text(encoding="utf-8"))


def find_forbidden_ai_output_keys(value: Any, *, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in FORBIDDEN_SEED_AI_OUTPUT_KEYS:
                findings.append(child_path)
            findings.extend(find_forbidden_ai_output_keys(child, path=child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(find_forbidden_ai_output_keys(child, path=f"{path}[{index}]"))
    return findings


async def seed_users(password: str) -> int:
    async with AsyncSessionLocal() as session:
        repo = UserRepository(session)
        for name, email, role in PILOT_USERS:
            await repo.upsert_dev_user(name=name, email=email, password_hash=hash_password(password), role=role)
        return len(PILOT_USERS)


async def seed_question_bank() -> int:
    items = _load_json_fixture("question_bank_items.json")
    forbidden = find_forbidden_ai_output_keys(items)
    if forbidden:
        raise RuntimeError(f"Question bank seed contains AI output fields: {', '.join(forbidden)}")

    count = 0
    async with AsyncSessionLocal() as session:
        for item in items:
            existing = await session.scalar(
                select(QuestionBankItem).where(
                    QuestionBankItem.job_family == item.get("job_family"),
                    QuestionBankItem.seniority == item.get("seniority"),
                    QuestionBankItem.question_type == item["question_type"],
                    QuestionBankItem.question == item["question"],
                )
            )
            if existing:
                existing.purpose = item["purpose"]
                existing.evaluation_criteria = item["evaluation_criteria"]
                existing.weight = item["weight"]
                existing.is_mandatory = item["is_mandatory"]
                existing.is_active = True
            else:
                session.add(QuestionBankItem(**item, is_active=True))
                count += 1
        await session.commit()
    return count


async def seed_draft_jobs_and_candidates() -> tuple[int, int]:
    templates = load_role_templates()
    candidates = _load_json_fixture("pilot_seed_candidates.json")
    forbidden = find_forbidden_ai_output_keys([template.model_dump(mode="json") for template in templates] + candidates)
    if forbidden:
        raise RuntimeError(f"Pilot seed contains AI output fields: {', '.join(forbidden)}")

    template_by_id = {template.template_id: template for template in templates}
    resume_root = Path(str(files("app.fixtures")))
    jobs_created = 0
    candidates_created = 0

    async with AsyncSessionLocal() as session:
        seeded_jobs: dict[str, Job] = {}
        for template in templates:
            title = f"Pilot Demo - {template.title}"
            job = await session.scalar(select(Job).where(Job.title == title))
            if not job:
                job = Job(
                    title=title,
                    department=template.department,
                    seniority=template.seniority_examples[0] if template.seniority_examples else None,
                    location="Pilot",
                    employment_type="Full-time",
                    salary_range=None,
                    raw_jd=template.raw_jd_starter,
                    improved_jd=None,
                    criteria_json=None,
                    must_haves_json=None,
                    nice_to_haves_json=None,
                    disqualifiers_json=None,
                    soft_skills_json=None,
                    knockout_areas_json=None,
                    status=JobStatus.DRAFT,
                    created_by_id=None,
                )
                session.add(job)
                await session.flush()
                jobs_created += 1
            seeded_jobs[template.template_id] = job

        for candidate_seed in candidates:
            template = template_by_id[candidate_seed["job_template_id"]]
            job = seeded_jobs[template.template_id]
            existing = await session.scalar(
                select(Candidate).where(Candidate.job_id == job.id, Candidate.email == candidate_seed["email"])
            )
            if existing:
                continue
            resume_path = resume_root / candidate_seed["resume_fixture"]
            resume_text = resume_path.read_text(encoding="utf-8")
            session.add(
                Candidate(
                    job_id=job.id,
                    name=candidate_seed["name"],
                    email=candidate_seed["email"],
                    phone=candidate_seed.get("phone"),
                    resume_file_path=str(resume_path),
                    resume_text=resume_text,
                    resume_hash=hashlib.sha256(resume_text.encode("utf-8")).hexdigest(),
                    parsed_profile_json=None,
                    enriched_profile_json=None,
                    status=CandidateStatus.UPLOADED,
                )
            )
            candidates_created += 1
        await session.commit()
    return jobs_created, candidates_created


async def main() -> None:
    password = os.getenv("PILOT_SEED_PASSWORD", "pilot-local-password")
    users = await seed_users(password)
    questions = await seed_question_bank()
    jobs, candidates = await seed_draft_jobs_and_candidates()
    print(f"Seeded/updated {users} pilot users.")
    print(f"Created {questions} question-bank items; existing items were updated in place.")
    print(f"Created {jobs} draft demo jobs and {candidates} candidate input records.")
    print("No AI scores, interview evaluations, final scorecards, or fake LLM outputs were seeded.")


if __name__ == "__main__":
    asyncio.run(main())
