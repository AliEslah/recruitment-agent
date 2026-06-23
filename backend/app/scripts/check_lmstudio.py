from __future__ import annotations

import asyncio
from pathlib import Path
import sys

from openai import AsyncOpenAI

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from app.core.config import Settings, get_settings  # noqa: E402
from app.core.errors import LLMUnavailableError  # noqa: E402
from app.services.lmstudio import LMStudioClient  # noqa: E402


def _print_recommendation(settings: Settings) -> None:
    print("recommended_fix:")
    if not settings.structured_llm_model:
        print("  - Set RECRUITING_LLM_MODEL to a loaded non-thinking LM Studio model.")
    else:
        print(f"  - {settings.lm_studio_unavailable_message}")
    print("  - Host backend: use LM_STUDIO_BASE_URL=http://localhost:1234/v1")
    print("  - Docker backend: use LM_STUDIO_BASE_URL=http://host.docker.internal:1234/v1")
    print("  - Confirm LM Studio is open, the local server is started, and the model is loaded.")


async def main() -> int:
    settings = get_settings()
    print(f"configured_base_url: {settings.lm_studio_base_url}")
    print(f"configured_model: {settings.structured_llm_model or '(unset)'}")
    print(f"timeout_seconds: {settings.lm_studio_timeout_seconds}")
    print(f"max_tokens: {settings.lm_studio_max_tokens}")
    print(f"enable_thinking: {settings.lm_studio_enable_thinking}")

    models_reachable = False
    model_loaded = False
    try:
        client = AsyncOpenAI(
            base_url=settings.lm_studio_base_url,
            api_key=settings.lm_studio_api_key,
            timeout=min(settings.lm_studio_timeout_seconds, 15),
        )
        models = await client.models.list()
        model_ids = [model.id for model in models.data]
        models_reachable = True
        model_loaded = settings.structured_llm_model in model_ids
        print("models_endpoint: reachable")
        print(f"loaded_models: {', '.join(model_ids) if model_ids else '(none reported)'}")
        print(f"configured_model_loaded: {model_loaded}")
    except Exception as exc:
        print("models_endpoint: unreachable")
        print(f"models_error: {exc}")
        _print_recommendation(settings)
        return 1

    if not settings.structured_llm_model:
        print("tiny_chat_completion: skipped")
        print("chat_error: RECRUITING_LLM_MODEL is required.")
        _print_recommendation(settings)
        return 1

    try:
        completion = await LMStudioClient(settings).chat_completion_with_usage(
            'Respond with exactly this JSON: {"ok": true}'
        )
        print("tiny_chat_completion: success")
        print(f"tiny_chat_content: {completion.content.strip()}")
        print(f"input_tokens: {completion.input_tokens}")
        print(f"output_tokens: {completion.output_tokens}")
    except LLMUnavailableError as exc:
        print("tiny_chat_completion: failed")
        print(f"chat_error: {exc.message}")
        _print_recommendation(settings)
        return 1
    except Exception as exc:
        print("tiny_chat_completion: failed")
        print(f"chat_error: {exc}")
        _print_recommendation(settings)
        return 1

    if models_reachable and not model_loaded:
        print("warning: configured model was not listed by /models. Load it in LM Studio or set RECRUITING_LLM_MODEL.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
