from __future__ import annotations

from app.agents.shared.utils import criteria_weight_total, normalize_criteria_weights


def test_criteria_weight_normalization() -> None:
    criteria = [{"name": "A", "weight": 2}, {"name": "B", "weight": 3}]

    normalized = normalize_criteria_weights(criteria)

    assert criteria_weight_total(normalized) == 100
    assert normalized[0]["weight"] == 40
    assert normalized[1]["weight"] == 60


def test_criteria_weight_normalization_handles_zero_total() -> None:
    normalized = normalize_criteria_weights([{"name": "A", "weight": 0}, {"name": "B", "weight": 0}])

    assert criteria_weight_total(normalized) == 100

