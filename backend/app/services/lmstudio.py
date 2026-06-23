from __future__ import annotations

from dataclasses import dataclass

from openai import AsyncOpenAI
from openai import APIConnectionError, APITimeoutError, OpenAIError

from app.core.config import Settings, get_settings
from app.core.errors import LLMUnavailableError


@dataclass(frozen=True)
class LMStudioCompletion:
    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None


class LMStudioClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        if not self.settings.structured_llm_model:
            raise LLMUnavailableError("RECRUITING_LLM_MODEL is required.")
        if self.settings.is_structured_model_thinking_only and not self.settings.recruiting_allow_thinking_model_for_json:
            raise LLMUnavailableError(
                "Configured model is thinking-only and is not suitable for structured JSON workflows. "
                "Use qwen/qwen3-4b-2507 with thinking disabled or another non-thinking model for RECRUITING_LLM_MODEL. "
                "Set RECRUITING_ALLOW_THINKING_MODEL_FOR_JSON=true only for slow experimental runs."
            )
        self.client = AsyncOpenAI(
            base_url=self.settings.lm_studio_base_url,
            api_key=self.settings.lm_studio_api_key,
            timeout=self.settings.lm_studio_timeout_seconds,
        )

    async def chat_completion_with_usage(self, prompt: str) -> LMStudioCompletion:
        try:
            request: dict = {
                "model": self.settings.structured_llm_model,
                "temperature": self.settings.lm_studio_temperature,
                "messages": [
                    {
                        "role": "system",
                        "content": "Return only valid JSON. Do not include markdown.",
                    },
                    {"role": "user", "content": prompt},
                ],
            }
            if self.settings.lm_studio_max_tokens:
                request["max_tokens"] = self.settings.lm_studio_max_tokens
            request["extra_body"] = {
                "chat_template_kwargs": {"enable_thinking": self.settings.lm_studio_enable_thinking},
                "enable_thinking": self.settings.lm_studio_enable_thinking,
            }
            response = await self.client.chat.completions.create(
                **request,
            )
        except (APIConnectionError, APITimeoutError):
            raise LLMUnavailableError(self.settings.lm_studio_unavailable_message) from None
        except OpenAIError as exc:
            raise LLMUnavailableError(f"{self.settings.lm_studio_unavailable_message} ({exc})") from exc
        choice = response.choices[0]
        message = choice.message
        content = message.content
        if not content:
            finish_reason = choice.finish_reason
            reasoning_content = getattr(message, "reasoning_content", None)
            detail = f"LM Studio returned an empty response. finish_reason={finish_reason}."
            if reasoning_content:
                detail += (
                    " The model emitted reasoning_content but no final JSON content. "
                    "For Qwen thinking models in LM Studio, disable thinking in the model prompt template "
                    "or use a non-thinking local model for structured JSON workflows."
                )
            if finish_reason == "length":
                detail += " The response exhausted LM_STUDIO_MAX_TOKENS before final JSON content was produced."
            raise LLMUnavailableError(detail)
        usage = getattr(response, "usage", None)
        input_tokens = getattr(usage, "prompt_tokens", None) if usage else None
        output_tokens = getattr(usage, "completion_tokens", None) if usage else None
        return LMStudioCompletion(content=content, input_tokens=input_tokens, output_tokens=output_tokens)

    async def chat_completion(self, prompt: str) -> str:
        return (await self.chat_completion_with_usage(prompt)).content

    async def health_check(self) -> str:
        return await self.chat_completion('Respond with exactly this JSON: {"ok": true}')
