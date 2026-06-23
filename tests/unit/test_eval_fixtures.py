from __future__ import annotations

from app.evaluation.fixtures import default_evals_root, load_eval_fixtures


def test_eval_fixture_loader_loads_at_least_five_job_families() -> None:
    fixture_sets = load_eval_fixtures(default_evals_root())

    assert len(fixture_sets) >= 5
    assert all(fixture.role["raw_jd"] for fixture in fixture_sets)
    assert all(fixture.candidates for fixture in fixture_sets)
    assert all(fixture.transcripts for fixture in fixture_sets)


def test_eval_fixture_loader_filters_by_role() -> None:
    fixture_sets = load_eval_fixtures(default_evals_root(), role="sales_account_executive")

    assert [fixture.role_id for fixture in fixture_sets] == ["sales_account_executive"]
    assert fixture_sets[0].candidates[0]["candidate_id"] == "sales-candidate-001"
