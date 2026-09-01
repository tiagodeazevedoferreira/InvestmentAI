from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from app.services.backtesting import BacktestConfig, Backtester
from app.services.evaluation import trading_metrics
from app.services.market_replay import MarketReplay
from app.services.ml_trading import purged_walk_forward_predictions
from app.services.openbb_market_data import OpenBBMarketDataProvider

SYMBOLS = ("PETR4", "VALE3", "ITUB4")
START = "2021-01-01"
END = "2026-09-01"
BASE_COMMISSION = 0.001
BASE_SLIPPAGE_BPS = 5.0
THRESHOLDS = (0.50, 0.55, 0.60, 0.65)
COST_GRID = ((0.0, 0.0), (0.001, 0.0), (0.001, 5.0), (0.001, 10.0), (0.002, 20.0))


def probability_to_long_only_signals(probabilities: pd.Series, threshold: float = 0.5) -> pd.Series:
    if not 0.5 <= threshold <= 1.0:
        raise ValueError("threshold must be between 0.5 and 1.0")
    p = probabilities.astype(float)
    if p.isna().any() or not ((p >= 0.0) & (p <= 1.0)).all():
        raise ValueError("probabilities must be finite and between 0 and 1")
    return p.ge(threshold).astype(int).replace({0: -1}).rename("signal")


def _run_backtest(frame: pd.DataFrame, signals: pd.Series, *, commission: float, slippage_bps: float):
    replay = MarketReplay("ML", frame)
    signal_iter = iter(signals.reindex(frame.index, fill_value=0).tolist())

    def signal_fn(_bar):
        return next(signal_iter)

    config = BacktestConfig(
        initial_cash=100_000.0,
        commission_rate=commission,
        slippage_bps=slippage_bps,
    )
    return Backtester(config).run(replay, signal_fn)


def yearly_metrics(equity: pd.Series) -> dict:
    year_end = equity.groupby(equity.index.year).last()
    starts = equity.groupby(equity.index.year).first()
    annual = year_end / starts - 1.0
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


def run_symbol(provider: OpenBBMarketDataProvider, symbol: str) -> dict:
    frame, quality = provider.historical_with_quality(symbol, start=START, end=END, interval="1d")
    prediction_run = purged_walk_forward_predictions(frame.rename(columns=str.title))
    eval_frame = frame.loc[prediction_run.predictions.index[0]:].copy()
    probabilities = prediction_run.probabilities.reindex(eval_frame.index)

    threshold_results = []
    for threshold in THRESHOLDS:
        signals = probability_to_long_only_signals(probabilities, threshold)
        result = _run_backtest(
            eval_frame,
            signals,
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

    base_signals = probability_to_long_only_signals(probabilities, 0.5)
    cost_results = []
    for commission, slippage_bps in COST_GRID:
        result = _run_backtest(
            eval_frame,
            base_signals,
            commission=commission,
            slippage_bps=slippage_bps,
        )
        cost_results.append(
            {
                "commission_rate": commission,
                "slippage_bps": slippage_bps,
                **trading_metrics(result.equity),
                "trades": result.trades,
                "final_cash": result.final_cash,
                "total_commission": result.total_commission,
                "total_slippage": result.total_slippage,
            }
        )

    base = threshold_results[0]
    return {
        "symbol": symbol,
        "rows": quality.rows,
        "evaluation_start": eval_frame.index[0].isoformat(),
        "evaluation_end": eval_frame.index[-1].isoformat(),
        "folds": prediction_run.folds,
        "prediction_rows": prediction_run.test_rows,
        "base_costs": {"commission_rate": BASE_COMMISSION, "slippage_bps": BASE_SLIPPAGE_BPS},
        "threshold_sensitivity": threshold_results,
        "cost_sensitivity": cost_results,
        "base_case": base,
    }


def main() -> None:
    provider = OpenBBMarketDataProvider()
    reports = [run_symbol(provider, symbol) for symbol in SYMBOLS]
    output = Path("artifacts/ml-robustness-audit.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(reports, indent=2), encoding="utf-8")
    print(json.dumps(reports, indent=2))


if __name__ == "__main__":
    main()
