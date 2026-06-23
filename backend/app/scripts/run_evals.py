from __future__ import annotations

import argparse
import asyncio
import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.candidate_processing.prompts import (
    CANDIDATE_SCORING_PROMPT_VERSION,
    RESUME_PARSING_PROMPT_VERSION,
    parse_resume_prompt,
    score_candidate_prompt,
)
from app.agents.final_decision.prompts import FINAL_SCORECARD_PROMPT_VERSION, final_scorecard_prompt
from app.agents.interview.prompts import (
    INTERVIEW_EVALUATION_PROMPT_VERSION,
    INTERVIEW_PLANNING_PROMPT_VERSION,
    interview_evaluation_prompt,
    interview_plan_prompt,
)
from app.agents.job_calibration.prompts import JOB_CALIBRATION_PROMPT_VERSION, jd_improvement_prompt, rubric_prompt
from app.agents.shared.utils import normalize_criteria_weights
from app.core.config import get_settings
from app.core.errors import LLMUnavailableError
from app.db.models import LlmCallLog
from app.db.session import AsyncSessionLocal
from app.evaluation.fixtures import RoleFixtureSet, default_evals_root, load_eval_fixtures
from app.evaluation.quality import (
    check_candidate_scoring,
    check_consistency,
    check_expected_recommendation_band,
    check_final_scorecard,
    check_interview_evaluation,
    check_interview_plan,
    check_job_calibration,
    check_resume_parsing,
)
from app.schemas.llm_outputs import (
    CandidateScoreOutput,
    FinalScorecardOutput,
    HiringRubricOutput,
    InterviewEvaluationOutput,
    InterviewPlanOutput,
    JDImprovementOutput,
    ParsedResumeOutput,
)
from app.services.llm_json import LLMJsonService

STAGES = (
    "job_calibration",
    "resume_parsing",
    "candidate_scoring",
    "interview_planning",
    "interview_evaluation",
    "final_scorecard",
)

PROMPT_VERSIONS = {
    "job_calibration": JOB_CALIBRATION_PROMPT_VERSION,
    "resume_parsing": RESUME_PARSING_PROMPT_VERSION,
    "candidate_scoring": CANDIDATE_SCORING_PROMPT_VERSION,
    "interview_planning": INTERVIEW_PLANNING_PROMPT_VERSION,
    "interview_evaluation": INTERVIEW_EVALUATION_PROMPT_VERSION,
    "final_scorecard": FINAL_SCORECARD_PROMPT_VERSION,
}

REPO_ROOT = Path(__file__).resolve().parents[3]


def public_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.name


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run local-LM evaluation quality checks.")
    parser.add_argument("--all", action="store_true", help="Run all evaluation stages.")
    parser.add_argument("--role", help="Run a single role fixture, for example sales_account_executive.")
    parser.add_argument("--stage", action="append", choices=STAGES, help="Run one stage. May be provided more than once.")
    parser.add_argument(
        "--dry-run-fixtures",
        action="store_true",
        help="Load and validate fixtures only. Does not instantiate LM Studio or the database.",
    )
    parser.add_argument("--evals-root", type=Path, default=default_evals_root(), help="Path to the evals directory.")
    return parser.parse_args()


def selected_stages(args: argparse.Namespace) -> tuple[str, ...]:
    if args.all or not args.stage:
        return STAGES
    return tuple(dict.fromkeys(args.stage))


def transcript_text(transcript: dict[str, Any]) -> str:
    messages = transcript.get("messages") or []
    return "\n".join(f"{item.get('role', 'unknown')}: {item.get('content', '')}" for item in messages)


def add_stage_result(
    report: dict[str, Any],
    *,
    role_id: str,
    family: str,
    stage: str,
    subject_id: str | None,
    output: dict[str, Any] | None,
    quality_warnings: list[dict[str, Any]] | None = None,
    evidence_grounding: list[dict[str, Any]] | None = None,
    consistency_warnings: list[dict[str, Any]] | None = None,
    expected: dict[str, Any] | None = None,
    error: str | None = None,
) -> None:
    quality_warnings = quality_warnings or []
    evidence_grounding = evidence_grounding or []
    consistency_warnings = consistency_warnings or []
    protected_warnings = [item for item in quality_warnings if item.get("code") == "protected_term"]
    unsupported_evidence = [item for item in evidence_grounding if item.get("status") == "unsupported"]
    failed = bool(error) or any(item.get("severity") == "error" for item in quality_warnings) or bool(unsupported_evidence)
    report["stage_results"].append(
        {
            "role": role_id,
            "family": family,
            "stage": stage,
            "subject_id": subject_id,
            "prompt_version": PROMPT_VERSIONS.get(stage),
            "passed": not failed,
            "error": error,
            "quality_warnings": quality_warnings,
            "evidence_grounding": evidence_grounding,
            "missing_evidence_issues": [
                item for item in quality_warnings if "missing" in str(item.get("code", ""))
            ],
            "hallucination_warnings": [
                item for item in quality_warnings if "unsupported" in str(item.get("code", "")) or "invented" in str(item.get("code", ""))
            ],
            "protected_attribute_warnings": protected_warnings,
            "consistency_warnings": consistency_warnings,
            "expected": expected or {},
            "raw_structured_output": output,
        }
    )


def output_score(output: dict[str, Any] | None) -> float | None:
    if not output:
        return None
    for key in ("overall_score", "overall_fit", "resume_score", "interview_score"):
        value = output.get(key)
        if isinstance(value, int | float):
            return float(value)
    return None


def output_recommendation(output: dict[str, Any] | None) -> str | None:
    if not output:
        return None
    recommendation = output.get("recommendation")
    return recommendation if isinstance(recommendation, str) else None


def summarize_report(report: dict[str, Any]) -> None:
    stage_results = report["stage_results"]
    total = len(stage_results)
    passed = sum(1 for item in stage_results if item["passed"])
    warning_count = sum(
        len(item["quality_warnings"]) + len(item["consistency_warnings"]) + len(item["evidence_grounding"])
        for item in stage_results
    )
    scores: dict[str, list[float]] = defaultdict(list)
    recommendations: Counter[str] = Counter()
    recommendations_by_stage: dict[str, Counter[str]] = defaultdict(Counter)
    for item in stage_results:
        score = output_score(item.get("raw_structured_output"))
        if score is not None:
            scores[item["stage"]].append(score)
        recommendation = output_recommendation(item.get("raw_structured_output"))
        if recommendation:
            recommendations[recommendation] += 1
            recommendations_by_stage[item["stage"]][recommendation] += 1
    report["summary"] = {
        "stage_results": total,
        "passed": passed,
        "failed": total - passed,
        "summary_score": round(passed / total, 3) if total else 0,
        "warning_count": warning_count,
        "score_distributions": {
            stage: {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": round(sum(values) / len(values), 2),
            }
            for stage, values in scores.items()
        },
        "recommendation_distribution": dict(recommendations),
        "recommendation_distribution_by_stage": {
            stage: dict(counter)
            for stage, counter in recommendations_by_stage.items()
        },
    }
    report["recommended_prompt_schema_fixes"] = recommended_fixes(stage_results)


def recommended_fixes(stage_results: list[dict[str, Any]]) -> list[str]:
    codes = Counter()
    for item in stage_results:
        for warning in item["quality_warnings"] + item["consistency_warnings"]:
            codes[warning.get("code", "unknown")] += 1
        for grounding in item["evidence_grounding"]:
            if grounding.get("status") == "unsupported":
                codes["unsupported_evidence"] += 1
    fixes = []
    if codes["criteria_score_missing_evidence"] or codes["unsupported_evidence"]:
        fixes.append("Tighten evidence instructions and require source-specific evidence spans for every score.")
    if codes["recommendation_score_mismatch"]:
        fixes.append("Clarify score-to-band calibration thresholds in candidate scoring prompts.")
    if codes["protected_term"]:
        fixes.append("Review protected-attribute guardrail wording and fixture source text.")
    if codes["interview_missing_evidence_empty"]:
        fixes.append("Require interview evaluators to list validation gaps even when the interview is positive.")
    if codes["missing_risk_in_final"]:
        fixes.append("Require final scorecards to explicitly carry forward major candidate and interview risks.")
    return fixes or ["No prompt/schema fixes were suggested by the heuristic checks."]


async def run_role(
    session: AsyncSession,
    service: LLMJsonService,
    fixture_set: RoleFixtureSet,
    stages_to_report: tuple[str, ...],
    report: dict[str, Any],
) -> None:
    role = fixture_set.role
    job_output: dict[str, Any] | None = None
    parsed_profiles: dict[str, dict[str, Any]] = {}
    candidate_scores: dict[str, dict[str, Any]] = {}
    interview_evaluations: dict[str, dict[str, Any]] = {}

    async def get_job_output() -> dict[str, Any]:
        nonlocal job_output
        if job_output is not None:
            return job_output
        jd = await service.generate(
            "job_calibration.improve_jd",
            jd_improvement_prompt(
                title=role["title"],
                raw_jd=role["raw_jd"],
                department=role.get("department"),
                seniority=role.get("seniority"),
            ),
            JDImprovementOutput,
            prompt_version=JOB_CALIBRATION_PROMPT_VERSION,
        )
        rubric = await service.generate(
            "job_calibration.extract_hiring_rubric",
            rubric_prompt(
                title=role["title"],
                improved_jd=jd.improved_jd,
                location=role.get("location"),
                employment_type=role.get("employment_type"),
            ),
            HiringRubricOutput,
            prompt_version=JOB_CALIBRATION_PROMPT_VERSION,
        )
        job_output = {
            "improved_jd": jd.improved_jd,
            "missing_info": jd.missing_info,
            "criteria": normalize_criteria_weights([item.model_dump(mode="json") for item in rubric.criteria]),
            "must_haves": rubric.must_haves,
            "nice_to_haves": rubric.nice_to_haves,
            "disqualifiers": rubric.disqualifiers,
            "soft_skills": rubric.soft_skills,
            "knockout_areas": rubric.knockout_areas,
        }
        return job_output

    async def get_parsed_profile(candidate: dict[str, Any]) -> dict[str, Any]:
        candidate_id = candidate["candidate_id"]
        if candidate_id in parsed_profiles:
            return parsed_profiles[candidate_id]
        parsed = await service.generate(
            "candidate_processing.parse_resume",
            parse_resume_prompt(candidate["resume_text"]),
            ParsedResumeOutput,
            prompt_version=RESUME_PARSING_PROMPT_VERSION,
        )
        parsed_profiles[candidate_id] = parsed.model_dump(mode="json")
        return parsed_profiles[candidate_id]

    async def get_candidate_score(candidate: dict[str, Any]) -> dict[str, Any]:
        candidate_id = candidate["candidate_id"]
        if candidate_id in candidate_scores:
            return candidate_scores[candidate_id]
        current_job_output = await get_job_output()
        profile = await get_parsed_profile(candidate)
        score = await service.generate(
            "candidate_processing.score_candidate",
            score_candidate_prompt(
                profile=profile,
                criteria=current_job_output.get("criteria", []),
                must_haves=current_job_output.get("must_haves", []),
                disqualifiers=current_job_output.get("disqualifiers", []),
            ),
            CandidateScoreOutput,
            prompt_version=CANDIDATE_SCORING_PROMPT_VERSION,
        )
        candidate_scores[candidate_id] = score.model_dump(mode="json")
        return candidate_scores[candidate_id]

    if "job_calibration" in stages_to_report:
        output = await get_job_output()
        add_stage_result(
            report,
            role_id=fixture_set.role_id,
            family=fixture_set.family,
            stage="job_calibration",
            subject_id=None,
            output=output,
            quality_warnings=check_job_calibration(output),
            expected=fixture_set.expected,
        )

    for candidate in fixture_set.candidates:
        candidate_id = candidate["candidate_id"]
        if "resume_parsing" in stages_to_report:
            profile = await get_parsed_profile(candidate)
            add_stage_result(
                report,
                role_id=fixture_set.role_id,
                family=fixture_set.family,
                stage="resume_parsing",
                subject_id=candidate_id,
                output=profile,
                quality_warnings=check_resume_parsing(profile, candidate["resume_text"]),
                evidence_grounding=[],
                expected=candidate,
            )
        if "candidate_scoring" in stages_to_report:
            score = await get_candidate_score(candidate)
            quality_warnings, grounding = check_candidate_scoring(score, candidate["resume_text"])
            quality_warnings.extend(check_expected_recommendation_band(score, candidate, location="candidate_score"))
            add_stage_result(
                report,
                role_id=fixture_set.role_id,
                family=fixture_set.family,
                stage="candidate_scoring",
                subject_id=candidate_id,
                output=score,
                quality_warnings=quality_warnings,
                evidence_grounding=grounding,
                expected=candidate,
            )
        if "interview_planning" in stages_to_report:
            current_job_output = await get_job_output()
            profile = await get_parsed_profile(candidate)
            score = await get_candidate_score(candidate)
            plan = await service.generate(
                "interview_planning.create_plan",
                interview_plan_prompt(
                    criteria=current_job_output.get("criteria", []),
                    profile=profile,
                    score=score,
                ),
                InterviewPlanOutput,
                prompt_version=INTERVIEW_PLANNING_PROMPT_VERSION,
            )
            output = plan.model_dump(mode="json")
            add_stage_result(
                report,
                role_id=fixture_set.role_id,
                family=fixture_set.family,
                stage="interview_planning",
                subject_id=candidate_id,
                output=output,
                quality_warnings=check_interview_plan(output),
                expected=candidate,
            )

    transcripts_by_candidate = {item["candidate_id"]: item for item in fixture_set.transcripts}
    for candidate in fixture_set.candidates:
        candidate_id = candidate["candidate_id"]
        transcript = transcripts_by_candidate.get(candidate_id)
        if not transcript:
            continue
        if "interview_evaluation" in stages_to_report:
            current_job_output = await get_job_output()
            profile = await get_parsed_profile(candidate)
            score = await get_candidate_score(candidate)
            evaluation = await service.generate(
                "interview_evaluation.evaluate",
                interview_evaluation_prompt(
                    transcript=transcript.get("messages", []),
                    criteria=current_job_output.get("criteria", []),
                    profile=profile,
                    resume_score=score,
                ),
                InterviewEvaluationOutput,
                prompt_version=INTERVIEW_EVALUATION_PROMPT_VERSION,
            )
            output = evaluation.model_dump(mode="json")
            interview_evaluations[candidate_id] = output
            quality_warnings, grounding = check_interview_evaluation(output, transcript_text(transcript))
            consistency = check_consistency(
                profile=profile,
                transcript_text=transcript_text(transcript),
                candidate_score=score,
                interview_evaluation=output,
            )
            add_stage_result(
                report,
                role_id=fixture_set.role_id,
                family=fixture_set.family,
                stage="interview_evaluation",
                subject_id=candidate_id,
                output=output,
                quality_warnings=quality_warnings,
                evidence_grounding=grounding,
                consistency_warnings=consistency,
                expected=transcript,
            )
        if "final_scorecard" in stages_to_report:
            profile = await get_parsed_profile(candidate)
            score = await get_candidate_score(candidate)
            evaluation = interview_evaluations.get(candidate_id)
            if evaluation is None:
                current_job_output = await get_job_output()
                evaluation_model = await service.generate(
                    "interview_evaluation.evaluate",
                    interview_evaluation_prompt(
                        transcript=transcript.get("messages", []),
                        criteria=current_job_output.get("criteria", []),
                        profile=profile,
                        resume_score=score,
                    ),
                    InterviewEvaluationOutput,
                    prompt_version=INTERVIEW_EVALUATION_PROMPT_VERSION,
                )
                evaluation = evaluation_model.model_dump(mode="json")
                interview_evaluations[candidate_id] = evaluation
            scorecard = await service.generate(
                "final_decision.generate_final_scorecard",
                final_scorecard_prompt(candidate_score=score, interview_evaluation=evaluation),
                FinalScorecardOutput,
                prompt_version=FINAL_SCORECARD_PROMPT_VERSION,
            )
            output = scorecard.model_dump(mode="json")
            consistency = check_consistency(
                profile=profile,
                transcript_text=transcript_text(transcript),
                candidate_score=score,
                interview_evaluation=evaluation,
                final_scorecard=output,
            )
            add_stage_result(
                report,
                role_id=fixture_set.role_id,
                family=fixture_set.family,
                stage="final_scorecard",
                subject_id=candidate_id,
                output=output,
                quality_warnings=check_final_scorecard(output),
                consistency_warnings=consistency,
                expected=transcript,
            )

    await session.commit()


def build_report(evals_root: Path, stages_to_report: tuple[str, ...]) -> dict[str, Any]:
    settings = get_settings()
    timestamp = datetime.now(UTC).replace(microsecond=0).isoformat()
    return {
        "timestamp": timestamp,
        "finished_at": None,
        "runtime_seconds": None,
        "lm_studio_model": settings.structured_llm_model,
        "lm_studio_base_url": settings.lm_studio_base_url,
        "prompt_versions": PROMPT_VERSIONS,
        "stages_run": list(stages_to_report),
        "evals_root": public_path(evals_root),
        "fixture_data_policy": (
            "Synthetic fixtures only. Reports must not contain real candidate data, raw tokens, OTPs, "
            "secrets, or private local paths."
        ),
        "stage_results": [],
        "summary": {},
        "recommended_prompt_schema_fixes": [],
        "run_status": "running",
        "error": None,
        "llm_call_usage": {
            "total_calls": 0,
            "cache_hits": 0,
            "uncached_calls": 0,
            "by_task": {},
            "error": None,
        },
    }


async def attach_llm_call_usage(report: dict[str, Any]) -> None:
    started_at = datetime.fromisoformat(report["timestamp"])
    finished_at = datetime.now(UTC).replace(microsecond=0)
    report["finished_at"] = finished_at.isoformat()
    report["runtime_seconds"] = round((finished_at - started_at).total_seconds(), 2)
    try:
        async with AsyncSessionLocal() as session:
            cache_rows = (
                await session.execute(
                    select(LlmCallLog.cache_hit, func.count())
                    .where(LlmCallLog.created_at >= started_at)
                    .group_by(LlmCallLog.cache_hit)
                )
            ).all()
            task_rows = (
                await session.execute(
                    select(LlmCallLog.task, LlmCallLog.cache_hit, func.count())
                    .where(LlmCallLog.created_at >= started_at)
                    .group_by(LlmCallLog.task, LlmCallLog.cache_hit)
                    .order_by(LlmCallLog.task, LlmCallLog.cache_hit)
                )
            ).all()
    except Exception as exc:
        report["llm_call_usage"]["error"] = f"{type(exc).__name__}: {exc}"
        return
    cache_hits = sum(int(count) for cache_hit, count in cache_rows if cache_hit)
    uncached_calls = sum(int(count) for cache_hit, count in cache_rows if not cache_hit)
    by_task: dict[str, dict[str, int]] = {}
    for task, cache_hit, count in task_rows:
        task_counts = by_task.setdefault(task, {"cache_hits": 0, "uncached_calls": 0, "total_calls": 0})
        key = "cache_hits" if cache_hit else "uncached_calls"
        task_counts[key] += int(count)
        task_counts["total_calls"] += int(count)
    report["llm_call_usage"] = {
        "total_calls": cache_hits + uncached_calls,
        "cache_hits": cache_hits,
        "uncached_calls": uncached_calls,
        "by_task": by_task,
        "error": None,
    }


def write_reports(report: dict[str, Any], reports_root: Path) -> tuple[Path, Path]:
    reports_root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.fromisoformat(report["timestamp"]).strftime("%Y%m%dT%H%M%SZ")
    json_path = reports_root / f"{timestamp}_eval_report.json"
    md_path = reports_root / f"{timestamp}_eval_report.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(render_markdown_report(report), encoding="utf-8")
    return json_path, md_path


def render_markdown_report(report: dict[str, Any]) -> str:
    summary = report.get("summary", {})
    lines = [
        "# Evaluation Quality Report",
        "",
        f"- Timestamp: {report['timestamp']}",
        f"- Model: {report.get('lm_studio_model') or '(unset)'}",
        f"- Stages run: {', '.join(report.get('stages_run', []))}",
        f"- Status: {report.get('run_status')}",
        f"- Finished at: {report.get('finished_at') or '(not recorded)'}",
        f"- Runtime seconds: {report.get('runtime_seconds') if report.get('runtime_seconds') is not None else '(not recorded)'}",
        f"- Summary score: {summary.get('summary_score', 0)}",
        f"- Passed/failed: {summary.get('passed', 0)}/{summary.get('failed', 0)}",
        f"- Fixture data policy: {report.get('fixture_data_policy', 'Synthetic fixtures only.')}",
        "",
        "## LLM Call Usage",
    ]
    usage = report.get("llm_call_usage") or {}
    lines.extend(
        [
            f"- Total calls: {usage.get('total_calls', 0)}",
            f"- Cache hits: {usage.get('cache_hits', 0)}",
            f"- Uncached calls: {usage.get('uncached_calls', 0)}",
        ]
    )
    if usage.get("error"):
        lines.append(f"- Usage query error: {usage['error']}")
    lines.extend(
        [
            "",
            "## Prompt Versions",
        ]
    )
    lines.extend(f"- {stage}: {version}" for stage, version in report.get("prompt_versions", {}).items())
    lines.extend(["", "## Role Results"])
    for item in report.get("stage_results", []):
        status = "PASS" if item["passed"] else "FAIL"
        subject = f" / {item['subject_id']}" if item.get("subject_id") else ""
        lines.append(f"- {status} {item['role']}{subject} / {item['stage']}")
        for warning in item["quality_warnings"][:5]:
            lines.append(f"  - {warning.get('severity', 'warning')}: {warning.get('code')} - {warning.get('message')}")
        unsupported = [entry for entry in item["evidence_grounding"] if entry.get("status") != "grounded"]
        for entry in unsupported[:3]:
            lines.append(
                f"  - evidence {entry.get('status')}: {entry.get('location')} "
                f"(overlap {entry.get('token_overlap')})"
            )
        for warning in item["consistency_warnings"][:3]:
            lines.append(f"  - consistency: {warning.get('code')} - {warning.get('message')}")
    lines.extend(["", "## Quality Warnings"])
    warning_total = summary.get("warning_count", 0)
    lines.append(f"- Total warning/check items: {warning_total}")
    lines.extend(["", "## Recommended Prompt/Schema Fixes"])
    lines.extend(f"- {item}" for item in report.get("recommended_prompt_schema_fixes", []))
    if report.get("error"):
        lines.extend(["", "## Run Error", "", report["error"]])
    lines.append("")
    return "\n".join(lines)


async def run(args: argparse.Namespace) -> int:
    fixtures = load_eval_fixtures(args.evals_root, role=args.role)
    if args.dry_run_fixtures:
        print(f"loaded_fixture_sets: {len(fixtures)}")
        for fixture_set in fixtures:
            print(
                f"- {fixture_set.role_id}: candidates={len(fixture_set.candidates)} "
                f"transcripts={len(fixture_set.transcripts)}"
            )
        return 0

    stages_to_report = selected_stages(args)
    report = build_report(args.evals_root, stages_to_report)
    reports_root = args.evals_root / "reports"
    try:
        async with AsyncSessionLocal() as session:
            service = LLMJsonService(session)
            for fixture_set in fixtures:
                await run_role(session, service, fixture_set, stages_to_report, report)
        report["run_status"] = "passed"
    except LLMUnavailableError as exc:
        report["run_status"] = "failed"
        report["error"] = (
            f"LM Studio was required for an uncached eval output and was unavailable: {exc.message}. "
            "No mock or fake LLM output was used."
        )
    except Exception as exc:
        report["run_status"] = "failed"
        report["error"] = f"Evaluation run failed: {type(exc).__name__}: {exc}"

    await attach_llm_call_usage(report)
    summarize_report(report)
    json_path, md_path = write_reports(report, reports_root)
    print(f"json_report: {json_path}")
    print(f"markdown_report: {md_path}")
    if report["run_status"] != "passed":
        print(report["error"])
        return 1
    return 0


def main() -> int:
    return asyncio.run(run(parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
