from __future__ import annotations

import pytest


EXTERNAL_MARKERS = {"db", "mailpit", "lmstudio", "e2e"}


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        marker_names = {marker.name for marker in item.iter_markers()}
        if not marker_names.intersection(EXTERNAL_MARKERS):
            item.add_marker(pytest.mark.unit)
