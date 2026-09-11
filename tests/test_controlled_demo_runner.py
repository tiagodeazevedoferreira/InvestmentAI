from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from backend.app.services.demo_portfolio_state import DemoPortfolioStateError, DemoPortfolioStateStore

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


def _snapshot(cash: float = 52_000.0) -> dict:
    return {
        "cash": cash,
        "positions": {"EURUSD": {"quantity": 0.01, "side": "BUY"}},
        "open_orders": [{"order_id": "123", "symbol": "EURUSD"}],
        "executions": [{"execution_id": "456", "order_id": "123", "symbol": "EURUSD", "quantity": 0.01}],
    }


def test_application_demo_portfolio_state_is_persistent(tmp_path: Path):
    store = DemoPortfolioStateStore(tmp_path / "portfolio.sqlite3")

    result = store.bootstrap(_snapshot())

    assert result["cash"] == pytest.approx(52_000.0)
    assert result["positions"]["EURUSD"]["quantity"] == pytest.approx(0.01)
    assert store.snapshot() == result


def test_bootstrap_does_not_overwrite_existing_application_state(tmp_path: Path):
    store = DemoPortfolioStateStore(tmp_path / "portfolio.sqlite3")
    first = store.bootstrap(_snapshot(52_000.0))

    second = store.bootstrap(_snapshot(51_000.0))

    assert second == first
    assert store.snapshot()["cash"] == pytest.approx(52_000.0)


def test_synchronize_updates_application_state_explicitly(tmp_path: Path):
    store = DemoPortfolioStateStore(tmp_path / "portfolio.sqlite3")
    store.bootstrap(_snapshot(52_000.0))

    result = store.synchronize(_snapshot(51_999.5))

    assert result["cash"] == pytest.approx(51_999.5)
    assert store.snapshot()["cash"] == pytest.approx(51_999.5)


def test_missing_application_state_is_fail_closed(tmp_path: Path):
    store = DemoPortfolioStateStore(tmp_path / "portfolio.sqlite3")

    with pytest.raises(DemoPortfolioStateError, match="not initialized"):
        store.snapshot()


def test_invalid_application_cash_is_rejected(tmp_path: Path):
    store = DemoPortfolioStateStore(tmp_path / "portfolio.sqlite3")

    with pytest.raises(DemoPortfolioStateError, match="numeric cash"):
        store.synchronize({"cash": "invalid", "positions": {}, "open_orders": [], "executions": []})
