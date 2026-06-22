from __future__ import annotations

from recruitment_agent.core.config import get_settings
from recruitment_agent.db.session import AsyncSessionLocal, engine


def test_database_session_wiring_imports() -> None:
    settings = get_settings()

    assert engine.url.render_as_string(hide_password=False) == settings.database.url
    assert engine is not None
    assert AsyncSessionLocal is not None
