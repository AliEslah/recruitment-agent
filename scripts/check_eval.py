from __future__ import annotations

from _check_utils import ROOT, run_all


def main() -> int:
    return run_all(
        [
            ("LM Studio health", ["uv", "run", "python", "-m", "app.scripts.check_lmstudio"], ROOT),
            ("full AI eval suite", ["uv", "run", "python", "-m", "app.scripts.run_evals", "--all"], ROOT),
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
