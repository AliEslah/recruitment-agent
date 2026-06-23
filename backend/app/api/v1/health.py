from __future__ import annotations

import time

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models import LlmCallLog
from app.db.session import get_session
from app.schemas.common import HealthResponse
from app.services.lmstudio import LMStudioClient
from app.services.llm_json import normalized_input_hash

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service=get_settings().app_name)


@router.get("/health/db", response_model=HealthResponse)
async def health_db(session: AsyncSession = Depends(get_session)) -> HealthResponse:
    await session.execute(text("select 1"))
    return HealthResponse(status="ok", service="postgres")


@router.get("/health/llm", response_model=HealthResponse)
async def health_llm(session: AsyncSession = Depends(get_session)) -> HealthResponse:
    settings = get_settings()
    prompt = 'Respond with exactly this JSON: {"ok": true}'
    input_hash = normalized_input_hash("health.llm", prompt, "HealthCheck", settings.structured_llm_model)
    started = time.perf_counter()
    input_tokens: int | None = None
    output_tokens: int | None = None
    log_status = "error"
    error: str | None = None
    try:
        completion = await LMStudioClient(settings).chat_completion_with_usage(prompt)
        input_tokens = completion.input_tokens
        output_tokens = completion.output_tokens
        log_status = "success"
    except Exception as exc:
        error = str(exc)
        raise
    finally:
        session.add(
            LlmCallLog(
                task="health.llm",
                model=settings.structured_llm_model,
                input_hash=input_hash,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=int((time.perf_counter() - started) * 1000),
                cache_hit=False,
                status=log_status,
                error=error,
            )
        )
        await session.commit()
    return HealthResponse(status="ok", service="lm-studio")
