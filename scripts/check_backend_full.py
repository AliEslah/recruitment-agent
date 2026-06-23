from __future__ import annotations

from _check_utils import ROOT, run_all


def main() -> int:
    return run_all(
        [
            ("backend tests", ["uv", "run", "pytest", "-q"], ROOT),
            ("backend lint", ["uv", "run", "ruff", "check", "backend/app", "tests"], ROOT),
            ("database migrations", ["uv", "run", "alembic", "upgrade", "head"], ROOT),
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
