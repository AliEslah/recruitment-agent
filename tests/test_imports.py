from __future__ import annotations


def test_core_modules_import() -> None:
    import app.main
    import app.core.config
    import app.db.session
    import app.agents.job_calibration.graph
    import app.agents.candidate_processing.graph
    import app.agents.interview.live_graph

    assert app.main.app is not None

