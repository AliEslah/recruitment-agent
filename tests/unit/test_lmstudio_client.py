from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.core.config import Settings
from app.core.errors import LLMUnavailableError
from app.services.lmstudio import LMStudioClient


def test_lmstudio_client_rejects_thinking_only_json_model() -> None:
    settings = Settings(
        RECRUITING_LLM_MODEL="qwen/qwen3-4b-thinking-2507",
        RECRUITING_ALLOW_THINKING_MODEL_FOR_JSON=False,
    )

    with pytest.raises(LLMUnavailableError, match="thinking-only"):
        LMStudioClient(settings)


def test_lmstudio_client_allows_hybrid_qwen_json_model() -> None:
    settings = Settings(RECRUITING_LLM_MODEL="qwen/qwen3-4b-2507")

    client = LMStudioClient(settings)

    assert client.settings.structured_llm_model == "qwen/qwen3-4b-2507"
    assert not client.settings.is_structured_model_thinking_only


class FakeCompletions:
    def __init__(self, response) -> None:
        self.response = response

    async def create(self, **_kwargs):
        return self.response


class FakeOpenAIClient:
    def __init__(self, response) -> None:
        self.chat = SimpleNamespace(completions=FakeCompletions(response))


@pytest.mark.asyncio
async def test_lmstudio_client_parses_usage_fields_when_present() -> None:
    response = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content='{"ok": true}'),
                finish_reason="stop",
            )
        ],
        usage=SimpleNamespace(prompt_tokens=12, completion_tokens=5),
    )
    client = LMStudioClient(Settings(RECRUITING_LLM_MODEL="test-model"))
    client.client = FakeOpenAIClient(response)

    completion = await client.chat_completion_with_usage("prompt")

    assert completion.content == '{"ok": true}'
    assert completion.input_tokens == 12
    assert completion.output_tokens == 5


@pytest.mark.asyncio
async def test_lmstudio_client_leaves_usage_fields_null_when_missing() -> None:
    response = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content='{"ok": true}'),
                finish_reason="stop",
            )
        ],
        usage=None,
    )
    client = LMStudioClient(Settings(RECRUITING_LLM_MODEL="test-model"))
    client.client = FakeOpenAIClient(response)

    completion = await client.chat_completion_with_usage("prompt")

    assert completion.input_tokens is None
    assert completion.output_tokens is None
