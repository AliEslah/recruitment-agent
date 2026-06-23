# Local LM Studio

The project is local-first. AI workflows call LM Studio through its local OpenAI-compatible API and do not fall back to cloud LLM providers.

## Recommended Model

Use:

```bash
RECRUITING_LLM_MODEL=qwen/qwen3-4b-2507
LM_STUDIO_BASE_URL=http://localhost:1234/v1
LM_STUDIO_API_KEY=lm-studio
LM_STUDIO_TEMPERATURE=0.2
LM_STUDIO_TIMEOUT_SECONDS=180
LM_STUDIO_MAX_TOKENS=2048
LM_STUDIO_ENABLE_THINKING=false
RECRUITING_ALLOW_THINKING_MODEL_FOR_JSON=false
```

When the backend runs in Docker, use:

```bash
LM_STUDIO_BASE_URL=http://host.docker.internal:1234/v1
```

## Thinking Model Boundary

Do not use `qwen/qwen3-4b-thinking-2507` as the default backend model. In observed LM Studio responses, thinking-only behavior can spend the response budget on reasoning metadata while leaving `message.content` empty. The backend needs concise JSON in `message.content` for structured workflows.

The backend sends `enable_thinking=false` for the hybrid `qwen/qwen3-4b-2507` model and blocks thinking-only model names by default. You can override that block with `RECRUITING_ALLOW_THINKING_MODEL_FOR_JSON=true` for deliberate experiments, but that path is expected to be slow and less reliable for JSON workflows.

## Health Check

```bash
uv run python -m app.scripts.check_lmstudio
curl http://localhost:8000/health/llm
```

The diagnostic checks the configured base URL and model, calls the local `/models` endpoint, runs a small real chat completion, and prints host-vs-Docker guidance when the server is unreachable.

If LM Studio is down, product flows fail clearly. They do not fabricate AI output and do not call cloud providers.
