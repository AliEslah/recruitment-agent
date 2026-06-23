# LM Studio Settings

This project uses LM Studio only through its local OpenAI-compatible API. Keep LM Studio model/runtime settings separate from backend project settings.

## Recommended Setup

Use one local model for structured JSON workflows:

```bash
RECRUITING_LLM_MODEL=qwen/qwen3-4b-2507
```

Use the base URL that matches where the backend runs:

```bash
# Backend running directly on host
LM_STUDIO_BASE_URL=http://localhost:1234/v1

# Backend running inside Docker
LM_STUDIO_BASE_URL=http://host.docker.internal:1234/v1
```

When FastAPI runs inside Docker, `localhost` is the backend container. Use `host.docker.internal` to reach LM Studio running on the host.

`RECRUITING_LLM_MODEL` is used by the backend for all structured JSON workflows:

- job calibration
- resume parsing
- candidate scoring
- interview planning
- interview evaluation
- final scorecards

## Why Not `qwen/qwen3-4b-thinking-2507` For JSON

The official Qwen and LM Studio model pages describe `qwen/qwen3-4b-thinking-2507` as a thinking-only model. In the observed LM Studio response, the model returned:

```json
{
  "content": "",
  "reasoning_content": "...2334 reasoning tokens...",
  "finish_reason": "stop"
}
```

That is bad for backend pipelines because the API result lives in `message.content`, while the model spends time and tokens in `reasoning_content`.

## Project Fail-Fast Guard

By default:

```bash
RECRUITING_ALLOW_THINKING_MODEL_FOR_JSON=false
```

If `RECRUITING_LLM_MODEL` contains a thinking-only model id such as `qwen/qwen3-4b-thinking-2507`, the backend returns a clear runtime error instead of waiting minutes per graph node.

Only override this for experiments:

```bash
RECRUITING_ALLOW_THINKING_MODEL_FOR_JSON=true
```

## LM Studio Runtime

For the structured JSON model:

- Load `qwen/qwen3-4b-2507`.
- Start the LM Studio local server.
- Keep LM Studio open while running AI flows.
- Confirm `/health/llm` returns `200` before job calibration, scoring, interview evaluation, or final scorecard generation.
- Keep backend request settings conservative:

```bash
LM_STUDIO_TEMPERATURE=0.2
LM_STUDIO_TIMEOUT_SECONDS=180
LM_STUDIO_MAX_TOKENS=2048
LM_STUDIO_ENABLE_THINKING=false
```

The backend sends `enable_thinking=false` as a best-effort request field, but this does not turn a thinking-only model into a non-thinking model.

## Diagnostic Command

From the repository root:

```bash
uv run python -m app.scripts.check_lmstudio
```

The script prints the configured base URL, configured model, whether `/models` is reachable, whether the configured model is loaded, and whether a tiny real chat completion succeeds. If it fails, follow the printed host-vs-Docker and model-loading recommendations.
