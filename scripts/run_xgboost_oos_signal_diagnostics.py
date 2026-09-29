from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from app.services.backtesting import BacktestConfig
from app.services.ci_market_data import CI_SYMBOLS, load_market_history
from app.services.xgboost_oos import run_xgboost_oos_backtest
from app.services.xgboost_oos_artifact import (
    load_xgboost_oos_artifact,
    validate_xgboost_oos_artifact_configuration,
)
from app.services.xgboost_oos_diagnostics import diagnose_xgboost_oos_signals


def run_symbol(
    symbol: str,
    *,
    horizon: int,
    train_size: int,
    test_size: int,
    step: int,
    threshold: float,
    initial_cash: float,
    oos_artifact_dir: str | None = None,
) -> dict:
    history, quality = load_market_history(
        symbol,
        source="provider",
        start="2021-09-15",
        end="2026-09-15",
        interval="1d",
    )
    expected = {
        "requested_start": "2021-09-15",
        "requested_end": "2026-09-15",
        "horizon": horizon,
        "train_size": train_size,
        "test_size": test_size,
        "step": step,
        "threshold": threshold,
        "initial_cash": initial_cash,
    }
    if oos_artifact_dir:
        oos, payload = load_xgboost_oos_artifact(
            Path(oos_artifact_dir) / f"{symbol.upper()}.json"
        )
        if str(payload.get("symbol", "")).upper() != symbol.upper():
            raise ValueError(f"OOS artifact symbol mismatch for {symbol}")
        validate_xgboost_oos_artifact_configuration(payload, expected)
    else:
        oos, _ = run_xgboost_oos_backtest(
            history,
            symbol=symbol,
            horizon=horizon,
            train_size=train_size,
            test_size=test_size,
            step=step,
            threshold=threshold,
            backtest_config=BacktestConfig(initial_cash=initial_cash),
        )

    diagnostics = diagnose_xgboost_oos_signals(
        history,
        symbol=symbol,
        oos=oos,
        threshold=threshold,
    )
    report = asdict(diagnostics)
    report["quality_valid"] = bool(quality.valid)
    report["oos_start"] = oos.probabilities.index.min().isoformat()
    report["oos_end"] = oos.probabilities.index.max().isoformat()
    periods = diagnostics.holding_periods_bars
    report["holding_period_summary"] = {
        "count": len(periods),
        "mean_bars": float(sum(periods) / len(periods)) if periods else None,
        "median_bars": float(sorted(periods)[len(periods) // 2]) if periods else None,
        "min_bars": min(periods) if periods else None,
        "max_bars": max(periods) if periods else None,
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Diagnose XGBoost OOS probabilities and signal behavior.")
    parser.add_argument("--horizon", type=int, default=5)
    parser.add_argument("--train-size", type=int, default=500)
    parser.add_argument("--test-size", type=int, default=100)
    parser.add_argument("--step", type=int, default=100)
    parser.add_argument("--threshold", type=float, default=0.60)
    parser.add_argument("--initial-cash", type=float, default=100000.0)
    parser.add_argument("--oos-artifact-dir", default=None)
    parser.add_argument(
        "--output",
        default="artifacts/xgboost-oos-signal-diagnostics/report.json",
    )
    args = parser.parse_args()

    reports = [
        run_symbol(
            symbol,
            horizon=args.horizon,
            train_size=args.train_size,
            test_size=args.test_size,
            step=args.step,
            threshold=args.threshold,
            initial_cash=args.initial_cash,
            oos_artifact_dir=args.oos_artifact_dir,
        )
        for symbol in CI_SYMBOLS
    ]
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(reports, indent=2, default=str), encoding="utf-8")
    print(json.dumps(reports, indent=2, default=str))


if __name__ == "__main__":
    main()
