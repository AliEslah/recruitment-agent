from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models import LlmCache, LlmCallLog
from app.services.lmstudio import LMStudioClient

T = TypeVar("T", bound=BaseModel)

SCHEMA_INSTRUCTIONS: dict[str, str] = {
    "JDImprovementOutput": (
        '{"improved_jd": string, "missing_info": [string], '
        '"suggested_clarifying_questions": [string]}'
    ),
    "HiringRubricOutput": (
        '{"criteria": [{"name": string, "description": string, "weight": number, '
        '"evidence_guidance": string}], "must_haves": [string], "nice_to_haves": [string], '
        '"disqualifiers": [string], "soft_skills": [string], "knockout_areas": [string]}'
    ),
    "ParsedResumeOutput": (
        '{"name": string|null, "email": string|null, "phone": string|null, "location": string|null, '
        '"years_of_experience": number|null, "seniority": string|null, "skills": [string], '
        '"work_experience": [{"company": string|null, "title": string|null, "start_date": string|null, '
        '"end_date": string|null, "responsibilities": [string], "achievements": [string]}], '
        '"education": [{"institution": string|null, "degree": string|null, "field": string|null, '
        '"year": string|null}], "certifications": [string], "projects": [string], '
        '"achievements": [string], "links": [string], "summary": string|null}'
    ),
    "CandidateScoreOutput": (
        '{"overall_score": number, "criteria_scores": [{"criterion_name": string, "score": number, '
        '"weight": number, "evidence": [string], "concerns": [string]}], "strengths": [string], '
        '"weaknesses": [string], "risks": [string], "recommendation": '
        '"STRONG_MATCH|POSSIBLE_MATCH|WEAK_MATCH|NEEDS_REVIEW", "confidence": number}'
    ),
    "InterviewPlanOutput": (
        '{"questions": [{"type": "FIXED|RESUME_VALIDATION|SOFT_SKILL|KNOCKOUT|DYNAMIC|FOLLOW_UP", '
        '"question": string, "purpose": string, "evaluation_criteria": string, '
        '"weight": number, "is_mandatory": boolean}]}'
    ),
    "FollowUpDecisionOutput": (
        '{"should_ask_follow_up": boolean, "follow_up_question": string|null, "reason": string, '
        '"next_action": "ASK_FOLLOW_UP|MOVE_NEXT|COMPLETE"}'
    ),
    "InterviewEvaluationOutput": (
        '{"overall_score": number, "competency_scores": object|array, "soft_skill_scores": object|array, '
        '"strengths": [string], "weaknesses": [string], "red_flags": [string], "evidence": object|array, '
        '"missing_evidence": [string], "recommendation": string, "confidence": number}'
    ),
    "FinalScorecardOutput": (
        '{"overall_fit": number, "resume_score": number, "interview_score": number, '
        '"soft_skill_score": number, "risk_level": string, "evidence_summary": object|array, '
        '"candidate_fit_narrative": string, "missing_evidence": [string], '
        '"recommendation": string, "confidence": number}'
    ),
}


def normalized_input_hash(
    task: str,
    prompt: str,
    schema_name: str,
    model: str = "",
    prompt_version: str | None = None,
) -> str:
    normalized = json.dumps(
        {"task": task, "prompt": prompt, "schema": schema_name, "model": model, "prompt_version": prompt_version},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def extract_json_object(text: str) -> Any:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.lower().startswith("json"):
            stripped = stripped[4:].strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    start_positions = [idx for idx in (stripped.find("{"), stripped.find("[")) if idx >= 0]
    if not start_positions:
        raise ValueError("No JSON object or array found in LLM output.")
    start = min(start_positions)
    opening = stripped[start]
    closing = "}" if opening == "{" else "]"
    end = stripped.rfind(closing)
    if end < start:
        raise ValueError("Malformed JSON boundaries in LLM output.")
    return json.loads(stripped[start : end + 1])


class LLMJsonService:
    def __init__(self, session: AsyncSession, client: LMStudioClient | None = None) -> None:
        self.session = session
        self.settings = get_settings()
        self.client = client or LMStudioClient(self.settings)

    async def generate(
        self,
        task: str,
        prompt: str,
        response_schema: type[T],
        prompt_version: str | None = None,
    ) -> T:
        input_hash = normalized_input_hash(
            task,
            prompt,
            response_schema.__name__,
            self.settings.structured_llm_model,
            prompt_version,
        )
        cached = await self.session.scalar(select(LlmCache).where(LlmCache.input_hash == input_hash))
        if cached:
            await self._log(
                task,
                input_hash,
                0,
                True,
                "success",
                None,
                None,
                metadata={"prompt_version": prompt_version},
            )
            await self.session.commit()
            return response_schema.model_validate(cached.output_json)

        full_prompt = self._json_prompt(prompt, response_schema)
        raw_response = ""
        started = time.perf_counter()
        input_tokens: int | None = None
        output_tokens: int | None = None
        try:
            completion = await self.client.chat_completion_with_usage(full_prompt)
            raw_response = completion.content
            input_tokens = completion.input_tokens
            output_tokens = completion.output_tokens
            parsed = response_schema.model_validate(extract_json_object(raw_response))
        except (ValidationError, ValueError) as first_exc:
            correction_prompt = (
                f"{full_prompt}\n\nYour previous response was invalid for schema "
                f"{response_schema.__name__}. Error: {first_exc}. Return corrected JSON only."
            )
            try:
                completion = await self.client.chat_completion_with_usage(correction_prompt)
                raw_response = completion.content
                input_tokens = completion.input_tokens
                output_tokens = completion.output_tokens
                parsed = response_schema.model_validate(extract_json_object(raw_response))
            except (ValidationError, ValueError) as second_exc:
                latency_ms = int((time.perf_counter() - started) * 1000)
                raw_path = self._write_raw_failure(task, input_hash, raw_response)
                await self._log(
                    task,
                    input_hash,
                    latency_ms,
                    False,
                    "validation_error",
                    str(second_exc),
                    raw_path,
                    input_tokens,
                    output_tokens,
                    metadata={"prompt_version": prompt_version},
                )
                await self.session.commit()
                raise
        except Exception as exc:
            latency_ms = int((time.perf_counter() - started) * 1000)
            await self._log(
                task,
                input_hash,
                latency_ms,
                False,
                "error",
                str(exc),
                None,
                input_tokens,
                output_tokens,
                metadata={"prompt_version": prompt_version},
            )
            await self.session.commit()
            raise

        latency_ms = int((time.perf_counter() - started) * 1000)
        self.session.add(
            LlmCache(
                task=task,
                input_hash=input_hash,
                model=self.settings.structured_llm_model,
                output_json=parsed.model_dump(mode="json"),
            )
        )
        await self._log(
            task,
            input_hash,
            latency_ms,
            False,
            "success",
            None,
            None,
            input_tokens,
            output_tokens,
            metadata={"prompt_version": prompt_version},
        )
        await self.session.commit()
        return parsed

    def _json_prompt(self, prompt: str, response_schema: type[BaseModel]) -> str:
        schema_instruction = SCHEMA_INSTRUCTIONS.get(response_schema.__name__)
        if not schema_instruction:
            schema_instruction = json.dumps(response_schema.model_json_schema(), separators=(",", ":"))
        return (
            f"{prompt}\n\nReturn JSON only with this shape:\n{schema_instruction}\n\n"
            "Do not use protected attributes for scoring. Provide evidence for scores. "
            "Provide confidence. Provide missing evidence. Recommend next step, but do not make final hiring decision."
        )

    async def _log(
        self,
        task: str,
        input_hash: str,
        latency_ms: int,
        cache_hit: bool,
        status: str,
        error: str | None,
        raw_response_path: str | None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.session.add(
            LlmCallLog(
                task=task,
                model=self.settings.structured_llm_model,
                input_hash=input_hash,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                cache_hit=cache_hit,
                status=status,
                error=error,
                raw_response_path=raw_response_path,
                metadata_json={
                    key: value
                    for key, value in (metadata or {}).items()
                    if value is not None
                }
                or None,
            )
        )

    def _write_raw_failure(self, task: str, input_hash: str, raw_response: str) -> str:
        folder = self.settings.data_dir / "llm_failures"
        folder.mkdir(parents=True, exist_ok=True)
        safe_task = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in task)
        path = Path(folder) / f"{safe_task}_{input_hash}.txt"
        path.write_text(raw_response, encoding="utf-8")
        return str(path)
