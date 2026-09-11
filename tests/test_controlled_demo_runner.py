from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_doto_mt5_controlled_demo.py"


def test_runner_is_read_only_by_default():
    env = os.environ.copy()
    env.pop("INVESTMENTAI_DEMO_EXECUTION_ARMED", None)
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--terminal", "missing-terminal.exe"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 1
    assert "CONTROLLED DEMO RUN: BLOCKED" in result.stdout
    assert "order_send: NOT CALLED" in result.stdout


def test_runner_execute_requires_explicit_arm():
    env = os.environ.copy()
    env.pop("INVESTMENTAI_DEMO_EXECUTION_ARMED", None)
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--execute"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 2
    assert "INVESTMENTAI_DEMO_EXECUTION_ARMED=true" in result.stdout
    assert "no broker submission attempted" in result.stdout
