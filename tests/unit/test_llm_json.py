from __future__ import annotations

import pytest
from pydantic import BaseModel

from app.db.models import LlmCallLog
from app.services.lmstudio import LMStudioCompletion
from app.services.llm_json import LLMJsonService
from app.services.llm_json import extract_json_object, normalized_input_hash


def test_llm_cache_key_is_stable() -> None:
    left = normalized_input_hash("task", "prompt", "Schema")
    right = normalized_input_hash("task", "prompt", "Schema")

    assert left == right
    assert len(left) == 64


def test_extract_json_helper_handles_markdown() -> None:
    assert extract_json_object('```json\n{"ok": true}\n```') == {"ok": True}


def test_extract_json_helper_handles_surrounding_text() -> None:
    assert extract_json_object('Here is JSON: {"score": 91}') == {"score": 91}


class SimpleOutput(BaseModel):
    ok: bool


class FakeSession:
    def __init__(self) -> None:
        self.added = []

    async def scalar(self, _query):
        return None

    def add(self, obj) -> None:
        self.added.append(obj)

    async def commit(self) -> None:
        return None


class FakeClient:
    def __init__(self, completion: LMStudioCompletion) -> None:
        self.completion = completion

    async def chat_completion_with_usage(self, _prompt: str) -> LMStudioCompletion:
        return self.completion


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("input_tokens", "output_tokens"),
    [
        (17, 9),
        (None, None),
    ],
)
async def test_llm_json_logs_usage_when_present_and_null_when_missing(
    input_tokens: int | None,
    output_tokens: int | None,
) -> None:
    session = FakeSession()
    service = LLMJsonService(
        session,
        client=FakeClient(LMStudioCompletion('{"ok": true}', input_tokens=input_tokens, output_tokens=output_tokens)),
    )

    result = await service.generate("unit.task", "Return ok.", SimpleOutput)

    llm_log = next(item for item in session.added if isinstance(item, LlmCallLog))
    assert result.ok is True
    assert llm_log.input_tokens == input_tokens
    assert llm_log.output_tokens == output_tokens
    assert llm_log.estimated_cost is None
