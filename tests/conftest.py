from __future__ import annotations

import os

import pytest


EXTERNAL_MARKERS = {"db", "mailpit", "lmstudio", "e2e", "slow"}
MARKER_ENV_GATES = {
    "db": "RUN_DB_TESTS",
    "mailpit": "RUN_MAILPIT_TESTS",
    "lmstudio": "RUN_LMSTUDIO_TESTS",
    "e2e": "RUN_E2E",
    "slow": "RUN_SLOW_TESTS",
}
TRUE_VALUES = {"1", "true", "yes", "on"}


def env_enabled(env_name: str) -> bool:
    return os.getenv(env_name, "").lower() in TRUE_VALUES


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        marker_names = {marker.name for marker in item.iter_markers()}
        if not marker_names.intersection(EXTERNAL_MARKERS):
            item.add_marker(pytest.mark.unit)
            continue

        disabled_markers = [
            f"{marker_name} ({env_name}=true)"
            for marker_name, env_name in MARKER_ENV_GATES.items()
            if marker_name in marker_names and not env_enabled(env_name)
        ]
        if disabled_markers:
            reason = "external/slow test disabled; set " + ", ".join(disabled_markers)
            item.add_marker(pytest.mark.skip(reason=reason))
