from __future__ import annotations

from _check_utils import ROOT, run_all


def main() -> int:
    return run_all(
        [
            ("backend lint", ["uv", "run", "ruff", "check", "backend/app", "tests"], ROOT),
            (
                "backend unit tests",
                [
                    "uv",
                    "run",
                    "pytest",
                    "-q",
                    "-m",
                    "unit and not lmstudio and not e2e and not mailpit and not slow",
                ],
                ROOT,
            ),
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
