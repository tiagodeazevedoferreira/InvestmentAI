from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

SYMBOLS = ("PETR4", "VALE3", "ITUB4")
BLOCK_SIZE = 5
BOOTSTRAP_REPLICATES = 10_000
RANDOM_SEED = 20261006


def _by_symbol(rows: list[dict]) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for row in rows:
        symbol = str(row.get("symbol", "")).upper()
        if symbol in result:
            raise ValueError(f"duplicate symbol: {symbol}")
        result[symbol] = row
    return result


def _observations(row: dict) -> tuple[np.ndarray, np.ndarray]:
    observations = row.get("conditional_return_observations_5d")
    if not isinstance(observations, list):
        raise ValueError("signal diagnostics missing conditional_return_observations_5d")
    long = np.array(
        [float(item["future_return_5d"]) for item in observations if item.get("regime") == "long"],
        dtype=float,
    )
    cash = np.array(
        [float(item["future_return_5d"]) for item in observations if item.get("regime") == "cash"],
        dtype=float,
    )
    if len(long) < BLOCK_SIZE or len(cash) < BLOCK_SIZE:
        raise ValueError("insufficient OOS observations for block bootstrap")
    return long, cash


def _block_bootstrap_mean_difference(
    long: np.ndarray,
    cash: np.ndarray,
    *,
    block_size: int = BLOCK_SIZE,
    replicates: int = BOOTSTRAP_REPLICATES,
    seed: int = RANDOM_SEED,
) -> np.ndarray:
    rng = np.random.default_rng(seed)

    def resample(values: np.ndarray) -> np.ndarray:
        starts = rng.integers(0, len(values), size=(int(np.ceil(len(values) / block_size)),))
        blocks = [
            values[(start + np.arange(block_size)) % len(values)]
            for start in starts
        ]
        return np.concatenate(blocks)[: len(values)]

    differences = np.empty(replicates, dtype=float)
    for index in range(replicates):
        differences[index] = resample(long).mean() - resample(cash).mean()
    return differences


def evaluate(signal_diagnostics: list[dict], cost_attribution: list[dict]) -> dict:
    signals = _by_symbol(signal_diagnostics)
    costs = _by_symbol([
        row for row in cost_attribution
        if str(row.get("scenario", "")).lower() == "commission_plus_slippage"
    ])
    if set(signals) != set(SYMBOLS) or set(costs) != set(SYMBOLS):
        raise ValueError("reports must contain exactly PETR4, VALE3 and ITUB4")

    rows = []
    for symbol in SYMBOLS:
        long, cash = _observations(signals[symbol])
        spread = float(long.mean() - cash.mean())
        bootstrap = _block_bootstrap_mean_difference(long, cash)
        ci_low, ci_high = np.quantile(bootstrap, [0.025, 0.975])
        std = float(bootstrap.std(ddof=1))
        cost = costs[symbol]
        trades = int(cost.get("trades", 0))
        total_commission = float(cost.get("total_commission", 0.0))
        total_slippage = float(cost.get("total_slippage", 0.0))
        total_cost = total_commission + total_slippage
        initial_cash = float(cost.get("initial_cash", 0.0))
        rows.append({
            "symbol": symbol,
            "long_rows": int(len(long)),
            "cash_rows": int(len(cash)),
            "observed_spread": spread,
            "bootstrap_ci_95_low": float(ci_low),
            "bootstrap_ci_95_high": float(ci_high),
            "bootstrap_std_error": std,
            "bootstrap_ci_excludes_zero": bool(ci_low > 0.0 or ci_high < 0.0),
            "bootstrap_probability_spread_le_zero": float(np.mean(bootstrap <= 0.0)),
            "zero_cost_strategy_return": float(cost.get("cost_impact_vs_zero_cost", 0.0) + cost.get("strategy_return", 0.0)),
            "after_cost_strategy_return": float(cost.get("strategy_return", 0.0)),
            "trades": trades,
            "total_commission": total_commission,
            "total_slippage": total_slippage,
            "total_transaction_cost": total_cost,
            "average_transaction_cost_per_trade": total_cost / trades if trades else None,
            "transaction_cost_pct_initial_cash": total_cost / initial_cash if initial_cash else None,
        })

    return {
        "question": "Is the fixed XGBoost OOS 5d long-versus-cash spread statistically defensible, and what transaction-cost burden is associated with the strategy?",
        "method": {
            "oos_only": True,
            "policy": "baseline_060",
            "threshold": 0.60,
            "horizon": "5d",
            "bootstrap": "circular block bootstrap",
            "block_size": BLOCK_SIZE,
            "replicates": BOOTSTRAP_REPLICATES,
            "seed": RANDOM_SEED,
            "selection_or_tuning": False,
            "interpretation": "Descriptive uncertainty diagnostic; the confidence interval is not a model-selection gate."
        },
        "symbols": rows,
        "summary": {
            "symbols_with_positive_observed_spread": sum(row["observed_spread"] > 0 for row in rows),
            "symbols_with_95pct_ci_above_zero": sum(row["bootstrap_ci_95_low"] > 0 for row in rows),
            "symbols_with_95pct_ci_below_zero": sum(row["bootstrap_ci_95_high"] < 0 for row in rows),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--signal-diagnostics", default="artifacts/xgboost-oos-signal-diagnostics/report.json")
    parser.add_argument("--cost-attribution", default="artifacts/xgboost-oos-cost-attribution/report.json")
    parser.add_argument("--output", default="artifacts/xgboost-oos-statistical-diagnosis/report.json")
    args = parser.parse_args()

    signals = json.loads(Path(args.signal_diagnostics).read_text(encoding="utf-8"))
    costs = json.loads(Path(args.cost_attribution).read_text(encoding="utf-8"))
    report = evaluate(signals, costs)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
