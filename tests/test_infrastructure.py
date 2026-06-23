from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_infrastructure_files_exist() -> None:
    expected_files = [
        "Dockerfile",
        ".dockerignore",
        "docker-compose.yml",
        ".env.example",
        ".env.test.example",
        "alembic/versions/20260622_0001_initial_recruiting_platform.py",
    ]

    for file_name in expected_files:
        assert (ROOT / file_name).is_file()


def test_docker_compose_declares_required_services() -> None:
    compose = (ROOT / "docker-compose.yml").read_text()

    assert "postgres:" in compose
    assert "mailpit:" in compose
    assert "backend:" in compose
    assert "host.docker.internal" in compose
    assert "condition: service_healthy" in compose


def test_env_template_includes_required_keys() -> None:
    env_example = (ROOT / ".env.example").read_text()

    for required_key in [
        "DATABASE_URL=",
        "LM_STUDIO_BASE_URL=",
        "RECRUITING_LLM_MODEL=",
        "RECRUITING_ALLOW_THINKING_MODEL_FOR_JSON=",
        "LM_STUDIO_API_KEY=",
        "LM_STUDIO_TEMPERATURE=",
        "LM_STUDIO_TIMEOUT_SECONDS=",
        "SMTP_HOST=",
        "SMTP_PORT=",
        "EMAIL_FROM=",
        "APP_BASE_URL=",
        "CORS_ALLOW_ORIGINS=",
        "JWT_SECRET_KEY=",
        "JWT_ALGORITHM=",
        "JWT_EXPIRE_MINUTES=",
        "DEV_ADMIN_EMAIL=",
        "DEV_ADMIN_PASSWORD=",
        "DEV_RECRUITER_EMAIL=",
        "DEV_RECRUITER_PASSWORD=",
        "DEV_MANAGER_EMAIL=",
        "DEV_MANAGER_PASSWORD=",
    ]:
        assert required_key in env_example
