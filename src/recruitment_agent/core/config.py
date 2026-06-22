from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


class AppSettings(EnvSettings):
    name: str = Field(default="Recruitment Agent", validation_alias="APP_NAME")
    environment: Literal["local", "test", "staging", "production"] = Field(
        default="local",
        validation_alias="ENVIRONMENT",
    )
    debug: bool = Field(default=False, validation_alias="APP_DEBUG")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")


class ApiSettings(EnvSettings):
    prefix: str = Field(default="/api/v1", validation_alias="API_V1_PREFIX")
    host: str = Field(default="0.0.0.0", validation_alias="API_HOST")
    port: int = Field(default=8000, validation_alias="API_PORT")
    cors_origins_raw: str = Field(default="", validation_alias="CORS_ORIGINS", exclude=True)

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]


class DatabaseSettings(EnvSettings):
    url: str = Field(
        default="postgresql+asyncpg://recruitment:recruitment@localhost:5432/recruitment",
        validation_alias="DATABASE_URL",
    )
    echo: bool = Field(default=False, validation_alias="DATABASE_ECHO")
    pool_size: int = Field(default=5, validation_alias="DATABASE_POOL_SIZE")
    max_overflow: int = Field(default=10, validation_alias="DATABASE_MAX_OVERFLOW")


class LangSmithSettings(EnvSettings):
    tracing: bool = Field(default=False, validation_alias="LANGSMITH_TRACING")
    project: str = Field(default="recruitment-agent", validation_alias="LANGSMITH_PROJECT")
    api_key: str | None = Field(default=None, validation_alias="LANGSMITH_API_KEY")
    endpoint: str = Field(default="https://api.smith.langchain.com", validation_alias="LANGSMITH_ENDPOINT")


class LLMSettings(EnvSettings):
    provider: str = Field(default="local", validation_alias="LLM_PROVIDER")
    model_name: str = Field(default="not-configured", validation_alias="LLM_MODEL_NAME")
    api_key: str | None = Field(default=None, validation_alias="LLM_API_KEY")
    temperature: float = Field(default=0.0, validation_alias="LLM_TEMPERATURE")


class Settings(BaseSettings):
    app: AppSettings = Field(default_factory=AppSettings)
    api: ApiSettings = Field(default_factory=ApiSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    langsmith: LangSmithSettings = Field(default_factory=LangSmithSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)

    model_config = SettingsConfigDict(
        extra="ignore",
        populate_by_name=True,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
