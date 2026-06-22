from __future__ import annotations

from recruitment_agent.core.config import Settings


def test_settings_defaults() -> None:
    settings = Settings()

    assert settings.app.name == "Recruitment Agent"
    assert settings.api.prefix == "/api/v1"
    assert settings.database.url.startswith("postgresql+asyncpg://")
    assert settings.langsmith.project == "recruitment-agent"
    assert settings.llm.provider == "local"


def test_settings_env_overrides(monkeypatch) -> None:
    monkeypatch.setenv("APP_NAME", "Hiring Ops")
    monkeypatch.setenv("API_PORT", "9000")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000,https://example.com")
    monkeypatch.setenv("DATABASE_POOL_SIZE", "2")
    monkeypatch.setenv("LLM_PROVIDER", "custom")
    monkeypatch.setenv("LLM_MODEL_NAME", "recruitment-model")

    settings = Settings()

    assert settings.app.name == "Hiring Ops"
    assert settings.api.port == 9000
    assert settings.api.cors_origins == ["http://localhost:3000", "https://example.com"]
    assert settings.database.pool_size == 2
    assert settings.llm.provider == "custom"
    assert settings.llm.model_name == "recruitment-model"
