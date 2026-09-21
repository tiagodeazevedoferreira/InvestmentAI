from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.services.backtesting import BacktestConfig
from app.services.ci_market_data import CI_SYMBOLS, load_market_history
from app.services.xgboost_oos import run_xgboost_oos_backtest
from app.services.xgboost_oos_artifact import write_xgboost_oos_artifact

START = "2021-09-15"
END = "2026-09-15"


def run_symbol(symbol: str, *, output_dir: Path, horizon: int, train_size: int, test_size: int, step: int, threshold: float, initial_cash: float) -> dict:
    history, quality = load_market_history(symbol, source="provider", start=START, end=END, interval="1d")
    oos, _ = run_xgboost_oos_backtest(history, symbol=symbol, horizon=horizon, train_size=train_size, test_size=test_size, step=step, threshold=threshold, backtest_config=BacktestConfig(initial_cash=initial_cash))
    path = write_xgboost_oos_artifact(output_dir / f"{symbol.upper()}.json", oos, symbol=symbol, configuration={"requested_start": START, "requested_end": END, "horizon": horizon, "train_size": train_size, "test_size": test_size, "step": step, "threshold": threshold, "initial_cash": initial_cash}, source={"provider": "openbb/yfinance", "interval": "1d", "rows": int(len(history)), "quality_valid": bool(quality.valid), "quality_report": quality.__dict__ if quality is not None else None})
    return {"symbol": symbol, "artifact": str(path), "rows": int(len(history)), "quality_valid": bool(quality.valid), "oos_folds": oos.folds, "oos_rows": oos.test_rows, "oos_start": oos.probabilities.index.min().isoformat(), "oos_end": oos.probabilities.index.max().isoformat()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--horizon", type=int, default=5)
    parser.add_argument("--train-size", type=int, default=500)
    parser.add_argument("--test-size", type=int, default=100)
    parser.add_argument("--step", type=int, default=100)
    parser.add_argument("--threshold", type=float, default=0.60)
    parser.add_argument("--initial-cash", type=float, default=100000.0)
    parser.add_argument("--output-dir", default="artifacts/xgboost-oos-shared")
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    reports = [run_symbol(symbol, output_dir=output_dir, horizon=args.horizon, train_size=args.train_size, test_size=args.test_size, step=args.step, threshold=args.threshold, initial_cash=args.initial_cash) for symbol in CI_SYMBOLS]
    manifest = {"schema_version": 1, "configuration": {"symbols": list(CI_SYMBOLS), "requested_start": START, "requested_end": END, "horizon": args.horizon, "train_size": args.train_size, "test_size": args.test_size, "step": args.step, "threshold": args.threshold, "initial_cash": args.initial_cash}, "symbols": reports}
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
