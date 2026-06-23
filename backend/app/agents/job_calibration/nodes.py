from __future__ import annotations

from app.agents.job_calibration.prompts import JOB_CALIBRATION_PROMPT_VERSION, jd_improvement_prompt, rubric_prompt
from app.agents.job_calibration.state import JobCalibrationState
from app.agents.shared.utils import criteria_weight_total, normalize_criteria_weights
from app.core.errors import ValidationAppError
from app.db.models import JobStatus
from app.repositories.jobs import JobRepository
from app.schemas.llm_outputs import HiringRubricOutput, JDImprovementOutput
from app.services.llm_json import LLMJsonService
from app.services.status_transitions import transition_job


async def load_job(state: JobCalibrationState) -> dict:
    job = await JobRepository(state["session"]).get(state["job_id"])
    return {
        "raw_jd": job.raw_jd,
        "title": job.title,
        "department": job.department,
        "seniority": job.seniority,
        "location": job.location,
        "employment_type": job.employment_type,
    }


async def improve_jd(state: JobCalibrationState) -> dict:
    output = await LLMJsonService(state["session"]).generate(
        "job_calibration.improve_jd",
        jd_improvement_prompt(
            title=state["title"],
            raw_jd=state["raw_jd"],
            department=state.get("department"),
            seniority=state.get("seniority"),
        ),
        JDImprovementOutput,
        prompt_version=JOB_CALIBRATION_PROMPT_VERSION,
    )
    return {"improved_jd": output.improved_jd, "missing_info": output.missing_info}


async def extract_hiring_rubric(state: JobCalibrationState) -> dict:
    output = await LLMJsonService(state["session"]).generate(
        "job_calibration.extract_hiring_rubric",
        rubric_prompt(
            title=state["title"],
            improved_jd=state["improved_jd"],
            location=state.get("location"),
            employment_type=state.get("employment_type"),
        ),
        HiringRubricOutput,
        prompt_version=JOB_CALIBRATION_PROMPT_VERSION,
    )
    return {
        "criteria": [item.model_dump(mode="json") for item in output.criteria],
        "must_haves": output.must_haves,
        "nice_to_haves": output.nice_to_haves,
        "disqualifiers": output.disqualifiers,
        "soft_skills": output.soft_skills,
        "knockout_areas": output.knockout_areas,
    }


async def normalize_criteria_weights_node(state: JobCalibrationState) -> dict:
    return {"criteria": normalize_criteria_weights(state.get("criteria", []))}


async def validate_rubric(state: JobCalibrationState) -> dict:
    criteria = state.get("criteria", [])
    if not criteria:
        raise ValidationAppError("Hiring rubric must include at least one criterion.")
    if criteria_weight_total(criteria) != 100:
        raise ValidationAppError("Hiring criteria weights must sum to 100.")
    return {}


async def persist_results(state: JobCalibrationState) -> dict:
    job = await JobRepository(state["session"]).get(state["job_id"])
    job.improved_jd = state["improved_jd"]
    job.criteria_json = state["criteria"]
    job.must_haves_json = state.get("must_haves", [])
    job.nice_to_haves_json = state.get("nice_to_haves", [])
    job.disqualifiers_json = state.get("disqualifiers", [])
    job.soft_skills_json = state.get("soft_skills", [])
    job.knockout_areas_json = state.get("knockout_areas", [])
    transition_job(job, JobStatus.CRITERIA_GENERATED)
    await state["session"].commit()
    return {}
