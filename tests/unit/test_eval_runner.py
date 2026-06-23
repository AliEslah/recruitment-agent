from __future__ import annotations

import argparse
import json

import pytest

from app.evaluation.fixtures import RoleFixtureSet, default_evals_root
from app.scripts import run_evals


@pytest.mark.asyncio
async def test_eval_runner_can_load_fixtures_without_lm_studio(capsys: pytest.CaptureFixture[str]) -> None:
    args = argparse.Namespace(
        all=False,
        role=None,
        stage=None,
        dry_run_fixtures=True,
        evals_root=default_evals_root(),
    )

    exit_code = await run_evals.run(args)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "loaded_fixture_sets" in captured.out


@pytest.mark.asyncio
async def test_eval_runner_fails_clearly_when_lm_studio_required_but_unavailable(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RECRUITING_LLM_MODEL", raising=False)
    fixture_set = RoleFixtureSet(
        role_id="sales_account_executive",
        family="sales",
        role={
            "title": "Sales Account Executive",
            "department": "Revenue",
            "seniority": "Mid-level",
            "location": "Remote",
            "employment_type": "Full-time",
            "raw_jd": "Sell B2B SaaS.",
            "expected_must_haves": [],
            "expected_nice_to_haves": [],
            "expected_soft_skills": [],
            "expected_disqualifiers": [],
            "expected_knockout_areas": [],
            "scoring_notes": "fixture only",
        },
        candidates=[],
        transcripts=[],
        expected={},
    )
    monkeypatch.setattr(run_evals, "load_eval_fixtures", lambda *_args, **_kwargs: [fixture_set])
    args = argparse.Namespace(
        all=True,
        role=None,
        stage=None,
        dry_run_fixtures=False,
        evals_root=tmp_path,
    )

    exit_code = await run_evals.run(args)

    reports = list((tmp_path / "reports").glob("*_eval_report.json"))
    assert exit_code == 1
    assert reports
    report = json.loads(reports[0].read_text(encoding="utf-8"))
    assert report["run_status"] == "failed"
    assert "No mock or fake LLM output was used" in report["error"]
