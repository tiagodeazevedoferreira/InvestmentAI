from __future__ import annotations

import argparse
import json
from pathlib import Path

SYMBOLS = ("PETR4", "VALE3", "ITUB4")
PREDICTIVE_HORIZON = "future_return_5d_mean"
AFTER_COST_SCENARIO = "commission_plus_slippage"


def _by_symbol(rows: list[dict]) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for row in rows:
        symbol = str(row.get("symbol", "")).upper()
        if symbol in result:
            raise ValueError(f"duplicate symbol: {symbol}")
        result[symbol] = row
    return result


def _predictive_row(row: dict) -> dict:
    conditional = row.get("conditional_returns")
    if not isinstance(conditional, dict):
        raise ValueError("signal diagnostics missing conditional_returns")
    long = conditional.get("long", {})
    cash = conditional.get("cash", {})
    long_mean = long.get(PREDICTIVE_HORIZON)
    cash_mean = cash.get(PREDICTIVE_HORIZON)
    if long_mean is None or cash_mean is None:
        raise ValueError("signal diagnostics missing 5d conditional returns")
    spread = float(long_mean) - float(cash_mean)
    return {
        "symbol": str(row["symbol"]).upper(),
        "oos_rows": int(row["oos_rows"]),
        "threshold": float(row["threshold"]),
        "long_rows": int(long.get("rows", 0)),
        "cash_rows": int(cash.get("rows", 0)),
        "long_mean_future_return_5d": float(long_mean),
        "cash_mean_future_return_5d": float(cash_mean),
        "long_minus_cash_future_return_5d": spread,
        "predictive_content_flag": spread > 0.0,
    }


def evaluate(signal_diagnostics: list[dict], economic: list[dict], cost: list[dict]) -> dict:
    signals = _by_symbol(signal_diagnostics)
    economics = _by_symbol(economic)
    after_cost_rows = [
        row for row in cost if str(row.get("scenario", "")).lower() == AFTER_COST_SCENARIO
    ]
    zero_cost_rows = [
        row for row in cost if str(row.get("scenario", "")).lower() == "zero_cost"
    ]
    after_costs = _by_symbol(after_cost_rows)
    zero_costs = _by_symbol(zero_cost_rows)
    if (
        set(signals) != set(SYMBOLS)
        or set(economics) != set(SYMBOLS)
        or set(after_costs) != set(SYMBOLS)
        or set(zero_costs) != set(SYMBOLS)
    ):
        raise ValueError("reports must contain exactly PETR4, VALE3 and ITUB4")
    if any(str(row.get("scenario", "")).lower() != AFTER_COST_SCENARIO for row in after_costs.values()):
        raise ValueError("cost report after-cost rows must use the commission_plus_slippage scenario")
    if any(str(row.get("scenario", "")).lower() != "zero_cost" for row in zero_costs.values()):
        raise ValueError("cost report zero-cost rows must use the zero_cost scenario")

    rows = []
    for symbol in SYMBOLS:
        predictive = _predictive_row(signals[symbol])
        economic_return = float(economics[symbol]["strategy_return"])
        zero_cost = float(zero_costs[symbol]["strategy_return"])
        after_cost = float(after_costs[symbol]["strategy_return"])
        cost_drag = after_cost - zero_cost
        if abs(economic_return - after_cost) > 1e-12:
            raise ValueError(f"economic/cost report drift for {symbol}")
        rows.append({
            **predictive,
            "zero_cost_strategy_return": zero_cost,
            "after_cost_strategy_return": after_cost,
            "cost_drag": cost_drag,
            "gross_strategy_positive": zero_cost > 0.0,
            "after_cost_strategy_positive": after_cost > 0.0,
            "diagnosis": (
                "predictive_signal_but_cost_unviable"
                if predictive["predictive_content_flag"] and zero_cost > 0.0 and after_cost <= 0.0
                else "positive_predictive_spread_and_positive_after_cost"
                if predictive["predictive_content_flag"] and after_cost > 0.0
                else "no_positive_5d_long_vs_cash_spread"
            ),
        })

    predictive_count = sum(bool(row["predictive_content_flag"]) for row in rows)
    gross_positive_count = sum(bool(row["gross_strategy_positive"]) for row in rows)
    after_cost_positive_count = sum(bool(row["after_cost_strategy_positive"]) for row in rows)
    return {
        "question": "Does the fixed XGBoost OOS signal show predictive content before costs, and where does the economic edge disappear?",
        "method": {
            "oos_only": True,
            "policy": "baseline_060",
            "threshold": 0.60,
            "predictive_horizon": "5d",
            "predictive_comparison": "mean future 5d return when probability >= 0.60 versus probability < 0.60",
            "economic_comparison": "zero-cost versus commission_plus_slippage strategy return",
            "selection_or_tuning": False,
        },
        "symbols": rows,
        "summary": {
            "symbols_with_positive_predictive_spread": predictive_count,
            "symbols_with_positive_zero_cost_strategy_return": gross_positive_count,
            "symbols_with_positive_after_cost_strategy_return": after_cost_positive_count,
        },
        "interpretation": (
            "Descriptive OOS diagnosis only. A positive predictive spread does not establish statistical significance, "
            "stability or tradability. The report does not select a policy or promote a model."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--signal-diagnostics", default="artifacts/xgboost-oos-signal-diagnostics/report.json")
    parser.add_argument("--economic-report", default="artifacts/xgboost-oos-economic-report/report.json")
    parser.add_argument("--cost-attribution", default="artifacts/xgboost-oos-cost-attribution/report.json")
    parser.add_argument("--output", default="artifacts/xgboost-oos-predictive-economic-diagnosis/report.json")
    args = parser.parse_args()

    signal_rows = json.loads(Path(args.signal_diagnostics).read_text(encoding="utf-8"))
    economic_rows = json.loads(Path(args.economic_report).read_text(encoding="utf-8"))
    cost_rows = json.loads(Path(args.cost_attribution).read_text(encoding="utf-8"))
    report = evaluate(signal_rows, economic_rows, cost_rows)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
