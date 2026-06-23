from __future__ import annotations

from _check_utils import FRONTEND, run_all


def main() -> int:
    return run_all(
        [
            ("frontend typecheck", ["npm", "run", "typecheck"], FRONTEND),
            ("frontend lint", ["npm", "run", "lint"], FRONTEND),
            ("frontend unit tests", ["npm", "run", "test"], FRONTEND),
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
