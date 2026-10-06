from __future__ import annotations

import argparse
import json
from pathlib import Path

CANONICAL_POLICY = {
    "name": "baseline_060",
    "entry_threshold": 0.60,
    "exit_threshold": 0.60,
    "confirmation_bars": 1,
}
CANONICAL_SCENARIO = "commission_plus_slippage"
REQUIRED_SYMBOLS = ("PETR4", "VALE3", "ITUB4")


def _load_rows(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"{path} must contain a JSON list")
    return payload


def _find_unique(rows: list[dict], **criteria: object) -> dict:
    matches = [
        row for row in rows
        if all(row.get(key) == value for key, value in criteria.items())
    ]
    if len(matches) != 1:
        raise ValueError(
            f"expected exactly one row for {criteria}, found {len(matches)}"
        )
    return matches[0]


def evaluate(economic_report: list[dict], persistence_report: list[dict]) -> dict:
    economic = {}
    persistence = {}

    for symbol in REQUIRED_SYMBOLS:
        row = _find_unique(
            economic_report,
            symbol=symbol,
            threshold=CANONICAL_POLICY["entry_threshold"],
        )
        if not bool(row.get("quality_valid")):
            raise ValueError(f"data quality is invalid for {symbol}")
        economic[symbol] = row

        persistent = _find_unique(
            persistence_report,
            symbol=symbol,
            name=CANONICAL_POLICY["name"],
            scenario=CANONICAL_SCENARIO,
            entry_threshold=CANONICAL_POLICY["entry_threshold"],
            exit_threshold=CANONICAL_POLICY["exit_threshold"],
            confirmation_bars=CANONICAL_POLICY["confirmation_bars"],
        )
        if not bool(persistent.get("quality_valid")):
            raise ValueError(f"persistence data quality is invalid for {symbol}")
        persistence[symbol] = persistent

    rows = []
    for symbol in REQUIRED_SYMBOLS:
        econ = economic[symbol]
        persistent = persistence[symbol]

        # The two reports must describe the same canonical economic replay.
        if abs(float(econ["strategy_return"]) - float(persistent["strategy_return"])) > 1e-12:
            raise ValueError(f"canonical strategy return mismatch for {symbol}")
        if int(econ["trades"]) != int(persistent["trades"]):
            raise ValueError(f"canonical trade count mismatch for {symbol}")

        after_cost_return = float(econ["strategy_return"])
        excess_vs_benchmark = float(econ["excess_return_vs_buy_hold"])
        passed = after_cost_return > 0.0 and excess_vs_benchmark > 0.0

        rows.append(
            {
                "symbol": symbol,
                "after_cost_return": after_cost_return,
                "benchmark_return": float(econ["benchmark_return"]),
                "excess_return_vs_buy_hold": excess_vs_benchmark,
                "max_drawdown": float(econ["max_drawdown"]),
                "trades": int(econ["trades"]),
                "passed": passed,
            }
        )

    failed_symbols = [row["symbol"] for row in rows if not row["passed"]]
    verdict = "PASS" if not failed_symbols else "FAIL"

    return {
        "verdict": verdict,
        "question": "Does the canonical XGBoost OOS signal remain economically exploitable out of sample after costs?",
        "decision_rule": {
            "policy": CANONICAL_POLICY,
            "cost_scenario": CANONICAL_SCENARIO,
            "requirements": [
                "positive strategy return after commission and slippage",
                "positive excess return versus buy-and-hold over the exact OOS replay window",
                "all required symbols must pass",
            ],
            "no_policy_selection": True,
            "no_threshold_tuning": True,
        },
        "symbols": rows,
        "failed_symbols": failed_symbols,
        "model_promotion_allowed": verdict == "PASS",
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate the pre-specified XGBoost OOS economic verdict without retraining or policy selection."
    )
    parser.add_argument(
        "--economic-report",
        default="artifacts/xgboost-oos-economic-report/report.json",
    )
    parser.add_argument(
        "--persistence-report",
        default="artifacts/xgboost-oos-signal-persistence/report.json",
    )
    parser.add_argument(
        "--output",
        default="artifacts/xgboost-oos-economic-verdict/report.json",
    )
    args = parser.parse_args()

    verdict = evaluate(
        _load_rows(Path(args.economic_report)),
        _load_rows(Path(args.persistence_report)),
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(verdict, indent=2), encoding="utf-8")
    print(json.dumps(verdict, indent=2))


if __name__ == "__main__":
    main()
