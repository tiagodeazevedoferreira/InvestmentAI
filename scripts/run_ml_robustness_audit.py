from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from app.services.backtesting import BacktestConfig, Backtester
from app.services.ci_market_data import CI_SYMBOLS, MarketDataSource, load_market_history
from app.services.evaluation import trading_metrics
from app.services.market_replay import MarketReplay
from app.services.ml_trading import probabilities_to_signals, signals_to_backtest_function
from app.services.xgboost_oos import purged_xgboost_oos_predictions
from app.services.features import build_features

SYMBOLS = CI_SYMBOLS
START = "2021-01-01"
END = "2026-09-01"
BASE_COMMISSION = 0.001
BASE_SLIPPAGE_BPS = 5.0
THRESHOLDS = (0.50, 0.55, 0.60, 0.65)
COST_GRID = ((0.0, 0.0), (0.001, 0.0), (0.001, 5.0), (0.001, 10.0), (0.002, 20.0))


def _run_backtest(
    frame: pd.DataFrame,
    probabilities: pd.Series,
    *,
    threshold: float,
    commission: float,
    slippage_bps: float,
):
    signals = probabilities_to_signals(probabilities, threshold=threshold)
    signal_fn = signals_to_backtest_function(signals)
    replay = MarketReplay("ML", frame)
    config = BacktestConfig(
        initial_cash=100_000.0,
        commission_rate=commission,
        slippage_bps=slippage_bps,
    )
    return Backtester(config).run(replay, signal_fn)


def _oos_replay_window(frame: pd.DataFrame, probabilities: pd.Series) -> pd.DataFrame:
    history_index = pd.DatetimeIndex(frame.index)
    if not history_index.is_unique:
        raise ValueError("history index must be unique")
    if not history_index.is_monotonic_increasing:
        raise ValueError("history index must be chronological")

    first_oos = pd.Timestamp(probabilities.index.min())
    last_oos = pd.Timestamp(probabilities.index.max())
    if first_oos not in history_index or last_oos not in history_index:
        raise ValueError("OOS prediction timestamps must be present in history")

    first_position = history_index.get_loc(first_oos)
    last_position = history_index.get_loc(last_oos)
    if not isinstance(first_position, int) or not isinstance(last_position, int):
        raise ValueError("history index lookup must resolve to unique positions")

    replay_end = last_position + 1
    if replay_end >= len(frame):
        raise ValueError("history must contain a bar after the final OOS prediction")

    return frame.iloc[first_position : replay_end + 1].copy()


def yearly_metrics(equity: pd.Series) -> dict:
    year_end = equity.groupby(equity.index.year).last()
    annual = year_end.pct_change().dropna()
    values = {str(year): float(value) for year, value in annual.items()}
    abs_total = sum(abs(value) for value in values.values())
    best = max(values.values()) if values else 0.0
    worst = min(values.values()) if values else 0.0
    concentration = abs(best) / abs_total if abs_total else 0.0
    return {
        "years": values,
        "positive_years": sum(value > 0 for value in values.values()),
        "negative_years": sum(value < 0 for value in values.values()),
        "best_year": best,
        "worst_year": worst,
        "return_concentration": concentration,
    }


def run_symbol(source: MarketDataSource, symbol: str) -> dict:
    frame, quality = load_market_history(symbol, source=source, start=START, end=END, interval="1d")
    assert quality is not None

    normalized = frame.rename(columns={column: str(column).title() for column in frame.columns})
    X, y = build_features(normalized, horizon=5)
    prediction_run = purged_xgboost_oos_predictions(
        X,
        y,
        horizon=5,
        train_size=500,
        test_size=100,
        step=100,
    )
    eval_frame = _oos_replay_window(frame, prediction_run.probabilities)
    probabilities = prediction_run.probabilities

    threshold_results = []
    for threshold in THRESHOLDS:
        result = _run_backtest(
            eval_frame,
            probabilities,
            threshold=threshold,
            commission=BASE_COMMISSION,
            slippage_bps=BASE_SLIPPAGE_BPS,
        )
        threshold_results.append(
            {
                "threshold": threshold,
                **trading_metrics(result.equity),
                "trades": result.trades,
                "final_cash": result.final_cash,
                "total_commission": result.total_commission,
                "total_slippage": result.total_slippage,
                **yearly_metrics(result.equity),
            }
        )

    cost_results = []
    for commission, slippage_bps in COST_GRID:
        result = _run_backtest(
            eval_frame,
            probabilities,
            threshold=0.60,
            commission=commission,
            slippage_bps=slippage_bps,
        )
        cost_results.append(
            {
                "threshold": 0.60,
                "commission_rate": commission,
                "slippage_bps": slippage_bps,
                **trading_metrics(result.equity),
                "trades": result.trades,
                "final_cash": result.final_cash,
                "total_commission": result.total_commission,
                "total_slippage": result.total_slippage,
            }
        )

    base = next(item for item in threshold_results if item["threshold"] == 0.60)
    return {
        "symbol": symbol,
        "source": source,
        "rows": quality.rows,
        "evaluation_start": eval_frame.index[0].isoformat(),
        "evaluation_end": eval_frame.index[-1].isoformat(),
        "folds": prediction_run.folds,
        "prediction_rows": prediction_run.test_rows,
        "model": "xgboost",
        "base_threshold": 0.60,
        "base_costs": {"commission_rate": BASE_COMMISSION, "slippage_bps": BASE_SLIPPAGE_BPS},
        "threshold_sensitivity": threshold_results,
        "cost_sensitivity": cost_results,
        "base_case": base,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run XGBoost OOS economic robustness audit.")
    parser.add_argument(
        "--source",
        choices=("fixture", "provider"),
        default="fixture",
        help="Data source. The deterministic fixture is the CI default; provider is an explicit external-data mode.",
    )
    args = parser.parse_args()
    source: MarketDataSource = args.source

    reports = [run_symbol(source, symbol) for symbol in SYMBOLS]
    output = Path("artifacts/ml-robustness-audit.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(reports, indent=2), encoding="utf-8")
    print(json.dumps(reports, indent=2))


if __name__ == "__main__":
    main()
