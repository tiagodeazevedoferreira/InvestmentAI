from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import numpy as np

SYMBOLS = ("PETR4", "VALE3", "ITUB4")
HORIZON = 5
THRESHOLD = 0.60
SCORE_BINS = (
    (0.0, 0.2, "[0.0,0.2)"),
    (0.2, 0.4, "[0.2,0.4)"),
    (0.4, 0.6, "[0.4,0.6)"),
    (0.6, 0.8, "[0.6,0.8)"),
    (0.8, 1.0, "[0.8,1.0]"),
)


def _by_symbol(rows: list[dict]) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for row in rows:
        symbol = str(row.get("symbol", "")).upper()
        if symbol in result:
            raise ValueError(f"duplicate symbol: {symbol}")
        result[symbol] = row
    return result


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _bin_for_score(score: float) -> tuple[float, float, str]:
    if not 0.0 <= score <= 1.0:
        raise ValueError(f"probability must be between 0 and 1, got {score}")
    for lower, upper, label in SCORE_BINS:
        if (lower <= score < upper) or (score == 1.0 and upper == 1.0):
            return lower, upper, label
    raise ValueError(f"unable to assign probability bin: {score}")


def _bucket_rows(predictions: list[dict], observations: list[dict]) -> list[dict]:
    returns_by_timestamp = {}
    for item in observations:
        timestamp = str(item["timestamp"])
        if timestamp in returns_by_timestamp:
            raise ValueError(f"duplicate observation timestamp: {timestamp}")
        returns_by_timestamp[timestamp] = float(item["future_return_5d"])

    rows = []
    seen = set()
    for prediction in predictions:
        timestamp = str(prediction["timestamp"])
        if timestamp in seen:
            raise ValueError(f"duplicate prediction timestamp: {timestamp}")
        seen.add(timestamp)
        if timestamp not in returns_by_timestamp:
            raise ValueError(f"missing future return for prediction timestamp: {timestamp}")
        score = float(prediction["probability"])
        lower, upper, label = _bin_for_score(score)
        rows.append(
            {
                "timestamp": timestamp,
                "probability": score,
                "future_return_5d": returns_by_timestamp[timestamp],
                "bin_lower": lower,
                "bin_upper": upper,
                "bin": label,
            }
        )
    if len(rows) != len(observations):
        raise ValueError(
            f"prediction/observation coverage mismatch: predictions={len(rows)} observations={len(observations)}"
        )
    return rows


def _summarize(rows: list[dict]) -> list[dict]:
    result = []
    for lower, upper, label in SCORE_BINS:
        values = np.array(
            [row["future_return_5d"] for row in rows if row["bin"] == label],
            dtype=float,
        )
        result.append(
            {
                "bin": label,
                "lower": lower,
                "upper": upper,
                "rows": int(len(values)),
                "mean_future_return_5d": float(values.mean()) if len(values) else None,
                "median_future_return_5d": float(np.median(values)) if len(values) else None,
                "std_future_return_5d": float(values.std(ddof=0)) if len(values) else None,
                "positive_return_fraction": float(np.mean(values > 0.0)) if len(values) else None,
            }
        )
    return result


def _monotonicity(summary: list[dict]) -> dict:
    means = [row["mean_future_return_5d"] for row in summary]
    available = [value for value in means if value is not None]
    adjacent_non_decreasing = [
        means[i + 1] >= means[i]
        for i in range(len(means) - 1)
        if means[i] is not None and means[i + 1] is not None
    ]
    return {
        "non_empty_bins": int(len(available)),
        "adjacent_comparisons": int(len(adjacent_non_decreasing)),
        "adjacent_non_decreasing_count": int(sum(adjacent_non_decreasing)),
        "adjacent_non_decreasing_fraction": (
            float(np.mean(adjacent_non_decreasing))
            if adjacent_non_decreasing
            else None
        ),
        "strictly_monotonic_increasing": bool(
            len(available) >= 2
            and all(
                means[i + 1] > means[i]
                for i in range(len(means) - 1)
                if means[i] is not None and means[i + 1] is not None
            )
        ),
    }


def evaluate(signal_diagnostics: list[dict], shared_artifacts: list[dict]) -> dict:
    signals = _by_symbol(signal_diagnostics)
    artifacts = _by_symbol(shared_artifacts)
    if set(signals) != set(SYMBOLS) or set(artifacts) != set(SYMBOLS):
        raise ValueError("reports must contain exactly PETR4, VALE3 and ITUB4")

    symbol_reports = []
    all_rows = []
    for symbol in SYMBOLS:
        observations = signals[symbol].get("conditional_return_observations_5d")
        predictions = artifacts[symbol].get("predictions")
        if not isinstance(observations, list):
            raise ValueError(f"{symbol}: missing conditional_return_observations_5d")
        if not isinstance(predictions, list):
            raise ValueError(f"{symbol}: missing predictions")
        rows = _bucket_rows(predictions, observations)
        summary = _summarize(rows)
        symbol_reports.append(
            {
                "symbol": symbol,
                "threshold": THRESHOLD,
                "horizon": HORIZON,
                "rows": len(rows),
                "bins": summary,
                "monotonicity": _monotonicity(summary),
            }
        )
        all_rows.extend(rows)

    overall_bins = _summarize(all_rows)
    return {
        "question": (
            "Does the fixed XGBoost OOS probability score show a monotonic "
            "relationship with future 5d returns across predefined fixed bins?"
        ),
        "method": {
            "oos_only": True,
            "policy": "baseline_060",
            "threshold": THRESHOLD,
            "horizon": HORIZON,
            "bins": [label for _, _, label in SCORE_BINS],
            "selection_or_tuning": False,
            "interpretation": (
                "Descriptive score informativeness diagnostic. Fixed bins are "
                "predefined and identical across symbols; results do not select "
                "a threshold, model, policy, or promotion decision."
            ),
        },
        "symbols": symbol_reports,
        "overall": {
            "rows": len(all_rows),
            "bins": overall_bins,
            "monotonicity": _monotonicity(overall_bins),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--signal-diagnostics",
        default="artifacts/xgboost-oos-signal-diagnostics/report.json",
    )
    parser.add_argument(
        "--shared-artifact-dir",
        default="artifacts/xgboost-oos-shared",
    )
    parser.add_argument(
        "--output",
        default="artifacts/xgboost-oos-score-bucket-diagnosis/report.json",
    )
    args = parser.parse_args()

    signals = json.loads(Path(args.signal_diagnostics).read_text(encoding="utf-8"))
    artifacts = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in (
            Path(args.shared_artifact_dir) / f"{symbol}.json"
            for symbol in SYMBOLS
        )
    ]
    report = evaluate(signals, artifacts)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
