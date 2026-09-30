from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from app.services.backtesting import BacktestConfig, Backtester
from app.services.ci_market_data import CI_SYMBOLS, load_market_history
from app.services.market_replay import MarketReplay
from app.services.xgboost_oos import XGBoostOOSRun
from app.services.xgboost_oos_artifact import (
    load_xgboost_oos_artifact,
    validate_xgboost_oos_artifact_configuration,
)
from app.services.xgboost_signal_persistence import probabilities_to_persistent_signals
from app.services.ml_trading import signals_to_backtest_function

COST_SCENARIOS = {
    "zero_cost": (0.0, 0.0),
    "commission_plus_slippage": (0.001, 5.0),
}

POLICIES = (
    {"name": "baseline_060", "entry_threshold": 0.60, "exit_threshold": 0.60, "confirmation_bars": 1},
    {"name": "confirm_060_2", "entry_threshold": 0.60, "exit_threshold": 0.60, "confirmation_bars": 2},
    {"name": "confirm_060_3", "entry_threshold": 0.60, "exit_threshold": 0.60, "confirmation_bars": 3},
    {"name": "hysteresis_070_055", "entry_threshold": 0.70, "exit_threshold": 0.55, "confirmation_bars": 1},
    {"name": "hysteresis_070_055_2", "entry_threshold": 0.70, "exit_threshold": 0.55, "confirmation_bars": 2},
)


def _max_drawdown(equity: pd.Series) -> float:
    peak = equity.cummax()
    return float((equity / peak - 1.0).min())


def _backtest(history: pd.DataFrame, symbol: str, oos: XGBoostOOSRun, policy: dict, config: BacktestConfig):
    signals = probabilities_to_persistent_signals(oos.probabilities, **{k: policy[k] for k in ("entry_threshold", "exit_threshold", "confirmation_bars")})
    signal_fn = signals_to_backtest_function(signals)
    replay_data = history.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"})
    history_index = pd.DatetimeIndex(replay_data.index)
    first_oos = pd.Timestamp(oos.probabilities.index.min())
    last_oos = pd.Timestamp(oos.probabilities.index.max())
    first_position = history_index.get_loc(first_oos)
    last_position = history_index.get_loc(last_oos)
    replay_data = replay_data.iloc[first_position:last_position + 2]
    return Backtester(config).run(MarketReplay(symbol=symbol, data=replay_data), signal_fn)


def run_symbol(symbol: str, *, initial_cash: float, horizon: int, train_size: int, test_size: int, step: int, oos_artifact_dir: str) -> list[dict]:
    history, quality = load_market_history(symbol, source="provider", start="2021-09-15", end="2026-09-15", interval="1d")
    expected = {"requested_start": "2021-09-15", "requested_end": "2026-09-15", "horizon": horizon, "train_size": train_size, "test_size": test_size, "step": step, "threshold": 0.60, "initial_cash": initial_cash}
    oos, payload = load_xgboost_oos_artifact(Path(oos_artifact_dir) / f"{symbol.upper()}.json")
    validate_xgboost_oos_artifact_configuration(payload, expected)
    rows: list[dict] = []
    for policy in POLICIES:
        for scenario, (commission_rate, slippage_bps) in COST_SCENARIOS.items():
            result = _backtest(history, symbol, oos, policy, BacktestConfig(initial_cash=initial_cash, commission_rate=commission_rate, slippage_bps=slippage_bps))
            rows.append({"symbol": symbol, **policy, "scenario": scenario, "commission_rate": commission_rate, "slippage_bps": slippage_bps, "quality_valid": bool(quality.valid), "oos_folds": oos.folds, "oos_rows": oos.test_rows, "oos_start": oos.probabilities.index.min().isoformat(), "oos_end": oos.probabilities.index.max().isoformat(), "initial_cash": initial_cash, "final_cash": result.final_cash, "strategy_return": result.final_cash / initial_cash - 1.0, "max_drawdown": _max_drawdown(result.equity), "trades": result.trades, "total_commission": result.total_commission, "total_slippage": result.total_slippage, "final_position": result.final_position})
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze XGBoost OOS signal persistence without retraining or selecting a policy.")
    parser.add_argument("--horizon", type=int, default=5)
    parser.add_argument("--train-size", type=int, default=500)
    parser.add_argument("--test-size", type=int, default=100)
    parser.add_argument("--step", type=int, default=100)
    parser.add_argument("--initial-cash", type=float, default=100000.0)
    parser.add_argument("--oos-artifact-dir", required=True)
    parser.add_argument("--output", default="artifacts/xgboost-oos-signal-persistence/report.json")
    args = parser.parse_args()
    reports: list[dict] = []
    for symbol in CI_SYMBOLS:
        reports.extend(run_symbol(symbol, initial_cash=args.initial_cash, horizon=args.horizon, train_size=args.train_size, test_size=args.test_size, step=args.step, oos_artifact_dir=args.oos_artifact_dir))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(reports, indent=2), encoding="utf-8")
    print(json.dumps(reports, indent=2))


if __name__ == "__main__":
    main()
