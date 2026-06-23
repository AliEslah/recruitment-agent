from __future__ import annotations

import os
import subprocess
from collections.abc import Iterable
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


Step = tuple[str, list[str], Path]


def run_step(label: str, command: list[str], cwd: Path) -> int:
    print(f"\n==> {label}", flush=True)
    print(f"+ {' '.join(command)}", flush=True)
    return subprocess.run(command, cwd=cwd, env=os.environ.copy()).returncode


def run_all(steps: Iterable[Step]) -> int:
    for label, command, cwd in steps:
        exit_code = run_step(label, command, cwd)
        if exit_code != 0:
            return exit_code
    return 0
