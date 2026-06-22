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
    ]

    for file_name in expected_files:
        assert (ROOT / file_name).is_file()


def test_docker_compose_declares_required_services() -> None:
    compose = (ROOT / "docker-compose.yml").read_text()

    assert "postgres:" in compose
    assert "image: postgres:17" in compose
    assert "api:" in compose
    assert "depends_on:" in compose
    assert "condition: service_healthy" in compose


def test_env_templates_include_required_keys() -> None:
    env_example = (ROOT / ".env.example").read_text()
    env_test_example = (ROOT / ".env.test.example").read_text()

    for required_key in [
        "DATABASE_URL=",
        "API_PORT=",
        "LANGSMITH_PROJECT=",
        "LLM_PROVIDER=",
        "LLM_MODEL_NAME=",
        "LLM_API_KEY=",
    ]:
        assert required_key in env_example
        assert required_key in env_test_example
