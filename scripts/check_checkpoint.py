from __future__ import annotations

from _check_utils import FRONTEND, ROOT, run_all


def main() -> int:
    return run_all(
        [
            (
                "backend tests excluding slow external suites",
                ["uv", "run", "pytest", "-q", "-m", "not lmstudio and not e2e and not mailpit and not slow"],
                ROOT,
            ),
            ("backend lint", ["uv", "run", "ruff", "check", "backend/app", "tests"], ROOT),
            ("frontend typecheck", ["npm", "run", "typecheck"], FRONTEND),
            ("frontend lint", ["npm", "run", "lint"], FRONTEND),
            ("frontend unit tests", ["npm", "run", "test"], FRONTEND),
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
