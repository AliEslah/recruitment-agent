from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    app_name: str = Field(default="AI Recruiting Decision Platform", validation_alias="APP_NAME")
    app_base_url: str = Field(default="http://localhost:8000", validation_alias="APP_BASE_URL")
    frontend_base_url: str = Field(default="http://localhost:3000", validation_alias="FRONTEND_BASE_URL")
    api_v1_prefix: str = Field(default="/api/v1", validation_alias="API_V1_PREFIX")
    debug: bool = Field(default=False, validation_alias="APP_DEBUG")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    cors_allow_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        validation_alias="CORS_ALLOW_ORIGINS",
    )

    database_url: str = Field(
        default="postgresql+asyncpg://recruitment:recruitment@localhost:5432/recruitment",
        validation_alias="DATABASE_URL",
    )
    database_echo: bool = Field(default=False, validation_alias="DATABASE_ECHO")

    lm_studio_base_url: str = Field(default="http://localhost:1234/v1", validation_alias="LM_STUDIO_BASE_URL")
    recruiting_llm_model: str = Field(default="", validation_alias="RECRUITING_LLM_MODEL")
    lm_studio_api_key: str = Field(default="lm-studio", validation_alias="LM_STUDIO_API_KEY")
    lm_studio_temperature: float = Field(default=0.2, validation_alias="LM_STUDIO_TEMPERATURE")
    lm_studio_timeout_seconds: float = Field(default=180, validation_alias="LM_STUDIO_TIMEOUT_SECONDS")
    lm_studio_max_tokens: int | None = Field(default=2048, validation_alias="LM_STUDIO_MAX_TOKENS")
    lm_studio_enable_thinking: bool = Field(default=False, validation_alias="LM_STUDIO_ENABLE_THINKING")
    recruiting_allow_thinking_model_for_json: bool = Field(
        default=False,
        validation_alias="RECRUITING_ALLOW_THINKING_MODEL_FOR_JSON",
    )

    smtp_host: str = Field(default="localhost", validation_alias="SMTP_HOST")
    smtp_port: int = Field(default=1025, validation_alias="SMTP_PORT")
    smtp_user: str | None = Field(default=None, validation_alias="SMTP_USER")
    smtp_pass: str | None = Field(default=None, validation_alias="SMTP_PASS")
    email_from: str = Field(default="recruiting@example.local", validation_alias="EMAIL_FROM")

    data_dir: Path = Field(default=Path("backend/data"), validation_alias="DATA_DIR")
    interview_token_ttl_hours: int = Field(default=72, validation_alias="INTERVIEW_TOKEN_TTL_HOURS")
    otp_ttl_minutes: int = Field(default=10, validation_alias="OTP_TTL_MINUTES")
    max_interview_follow_ups: int = Field(default=2, validation_alias="MAX_INTERVIEW_FOLLOW_UPS")

    jwt_secret_key: str = Field(default="change-me-local-dev-only-32-bytes-minimum", validation_alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=1440, validation_alias="JWT_EXPIRE_MINUTES")

    dev_admin_email: str | None = Field(default=None, validation_alias="DEV_ADMIN_EMAIL")
    dev_admin_password: str | None = Field(default=None, validation_alias="DEV_ADMIN_PASSWORD")
    dev_recruiter_email: str | None = Field(default=None, validation_alias="DEV_RECRUITER_EMAIL")
    dev_recruiter_password: str | None = Field(default=None, validation_alias="DEV_RECRUITER_PASSWORD")
    dev_manager_email: str | None = Field(default=None, validation_alias="DEV_MANAGER_EMAIL")
    dev_manager_password: str | None = Field(default=None, validation_alias="DEV_MANAGER_PASSWORD")

    @property
    def lm_studio_unavailable_message(self) -> str:
        model = self.structured_llm_model or "(unset)"
        message = (
            f"LM Studio is not reachable at {self.lm_studio_base_url} for model {model}. "
            "Open LM Studio, start the local server, and load the configured model."
        )
        parsed = urlparse(self.lm_studio_base_url)
        if parsed.hostname in {"localhost", "127.0.0.1", "::1"}:
            message += (
                " If the backend is running in Docker, localhost points to the backend container; "
                "set LM_STUDIO_BASE_URL=http://host.docker.internal:1234/v1 and recreate the backend container."
            )
        return message

    @property
    def structured_llm_model(self) -> str:
        return self.recruiting_llm_model

    def candidate_interview_url(self, token: str) -> str:
        return f"{self.frontend_base_url.rstrip('/')}/candidate/interview/{token}"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]

    @property
    def is_structured_model_thinking_only(self) -> bool:
        model = self.structured_llm_model.lower()
        return "thinking-2507" in model or model.endswith("-thinking")


@lru_cache
def get_settings() -> Settings:
    return Settings()
