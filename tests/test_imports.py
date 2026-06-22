from __future__ import annotations


def test_core_modules_import() -> None:
    import recruitment_agent.main
    import recruitment_agent.core.config
    import recruitment_agent.db.session
    import recruitment_agent.agents.graph

    assert recruitment_agent.main.app is not None
