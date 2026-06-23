from __future__ import annotations

from app.core.config import Settings


def test_settings_defaults() -> None:
    settings = Settings()

    assert settings.app_name == "AI Recruiting Decision Platform"
    assert settings.api_v1_prefix == "/api/v1"
    assert settings.frontend_base_url == "http://localhost:3000"
    assert settings.candidate_interview_url("token-value") == "http://localhost:3000/candidate/interview/token-value"
    assert settings.database_url.startswith("postgresql+asyncpg://")
    assert "http://localhost:3000" in settings.cors_origins
    assert settings.lm_studio_base_url == "http://localhost:1234/v1"
    assert settings.lm_studio_api_key == "lm-studio"
    assert settings.lm_studio_temperature == 0.2
    assert settings.structured_llm_model == ""
    assert not settings.recruiting_allow_thinking_model_for_json
    assert settings.jwt_algorithm == "HS256"
    assert settings.jwt_expire_minutes == 1440


def test_settings_env_overrides(monkeypatch) -> None:
    monkeypatch.setenv("RECRUITING_LLM_MODEL", "local-model")
    monkeypatch.setenv("SMTP_PORT", "2525")
    monkeypatch.setenv("APP_BASE_URL", "http://example.test")
    monkeypatch.setenv("FRONTEND_BASE_URL", "http://frontend.example.test/")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-with-at-least-32-bytes")
    monkeypatch.setenv("JWT_EXPIRE_MINUTES", "30")

    settings = Settings()

    assert settings.structured_llm_model == "local-model"
    assert settings.smtp_port == 2525
    assert settings.app_base_url == "http://example.test"
    assert settings.candidate_interview_url("abc") == "http://frontend.example.test/candidate/interview/abc"
    assert settings.jwt_secret_key == "test-secret-key-with-at-least-32-bytes"
    assert settings.jwt_expire_minutes == 30


def test_thinking_only_model_detection() -> None:
    settings = Settings(RECRUITING_LLM_MODEL="qwen/qwen3-4b-thinking-2507")

    assert settings.is_structured_model_thinking_only


def test_hybrid_qwen_model_is_allowed_for_structured_json() -> None:
    settings = Settings(RECRUITING_LLM_MODEL="qwen/qwen3-4b-2507")

    assert not settings.is_structured_model_thinking_only
