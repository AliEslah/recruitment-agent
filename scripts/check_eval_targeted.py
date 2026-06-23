from __future__ import annotations

import argparse

from _check_utils import ROOT, Step, run_all


DEFAULT_STAGES = ("candidate_scoring", "interview_evaluation", "final_scorecard")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run targeted real LM Studio evaluation stages.")
    parser.add_argument(
        "--stage",
        action="append",
        dest="stages",
        help="Eval stage to run. May be repeated. Defaults to candidate/interview/final scoring stages.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    stages = tuple(args.stages or DEFAULT_STAGES)
    steps: list[Step] = [("LM Studio health", ["uv", "run", "python", "-m", "app.scripts.check_lmstudio"], ROOT)]
    steps.extend(
        (
            f"AI eval stage: {stage}",
            ["uv", "run", "python", "-m", "app.scripts.run_evals", "--stage", stage],
            ROOT,
        )
        for stage in stages
    )
    return run_all(steps)


if __name__ == "__main__":
    raise SystemExit(main())
