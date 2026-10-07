from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import numpy as np

SYMBOLS = ("PETR4", "VALE3", "ITUB4")
EXPECTED_FOLDS = 7
HORIZON = 5
THRESHOLD = 0.60
BLOCK_SIZE = 5
BOOTSTRAP_REPLICATES = 2_000
RANDOM_SEED = 20261007


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


def _rankdata(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty(len(values), dtype=float)
    sorted_values = values[order]
    start = 0
    while start < len(values):
        end = start + 1
        while end < len(values) and sorted_values[end] == sorted_values[start]:
            end += 1
        ranks[order[start:end]] = (start + 1 + end) / 2.0
        start = end
    return ranks


def _pearson(x: np.ndarray, y: np.ndarray) -> float | None:
    if len(x) < 2:
        return None
    x_centered = x - x.mean()
    y_centered = y - y.mean()
    denominator = float(np.sqrt(np.sum(x_centered**2) * np.sum(y_centered**2)))
    if denominator == 0.0:
        return None
    return float(np.sum(x_centered * y_centered) / denominator)


def _spearman(x: np.ndarray, y: np.ndarray) -> float | None:
    return _pearson(_rankdata(x), _rankdata(y))


def _paired_rows(signal: dict, artifact: dict) -> list[dict]:
    observations = signal.get("conditional_return_observations_5d")
    predictions = artifact.get("predictions")
    if not isinstance(observations, list):
        raise ValueError("signal diagnostics missing conditional_return_observations_5d")
    if not isinstance(predictions, list):
        raise ValueError("shared artifact missing predictions")

    returns_by_timestamp: dict[str, float] = {}
    for item in observations:
        timestamp = str(item["timestamp"])
        if timestamp in returns_by_timestamp:
            raise ValueError(f"duplicate observation timestamp: {timestamp}")
        returns_by_timestamp[timestamp] = float(item["future_return_5d"])

    rows: list[dict] = []
    seen: set[str] = set()
    for prediction in predictions:
        timestamp = str(prediction["timestamp"])
        if timestamp in seen:
            raise ValueError(f"duplicate prediction timestamp: {timestamp}")
        seen.add(timestamp)
        if timestamp not in returns_by_timestamp:
            raise ValueError(f"missing future return for prediction timestamp: {timestamp}")
        rows.append({
            "timestamp": timestamp,
            "probability": float(prediction["probability"]),
            "future_return_5d": returns_by_timestamp[timestamp],
        })

    if len(rows) != len(observations):
        raise ValueError(
            f"prediction/observation coverage mismatch: predictions={len(rows)} observations={len(observations)}"
        )
    return rows


def _fold_rows(rows: list[dict], fold: dict) -> list[dict]:
    start = _parse_timestamp(str(fold["test_start"]))
    end = _parse_timestamp(str(fold["test_end"]))
    selected = [
        row for row in rows
        if start <= _parse_timestamp(str(row["timestamp"])) <= end
    ]
    if len(selected) != 100:
        raise ValueError(f"fold {fold['fold']} expected 100 observations, got {len(selected)}")
    return selected


def _circular_block_indices(length: int, block_size: int, rng: np.random.Generator) -> np.ndarray:
    starts = rng.integers(0, length, size=int(np.ceil(length / block_size)))
    return np.concatenate(
        [(start + np.arange(block_size)) % length for start in starts]
    )[:length]


def _bootstrap_spearman(
    scores: np.ndarray,
    returns: np.ndarray,
    *,
    block_size: int = BLOCK_SIZE,
    replicates: int = BOOTSTRAP_REPLICATES,
    seed: int = RANDOM_SEED,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    values = np.empty(replicates, dtype=float)
    for index in range(replicates):
        sample = _circular_block_indices(len(scores), block_size, rng)
        correlation = _spearman(scores[sample], returns[sample])
        values[index] = np.nan if correlation is None else correlation
    return values[~np.isnan(values)]


def _metrics(rows: list[dict], *, bootstrap: bool, seed: int) -> dict:
    scores = np.array([float(row["probability"]) for row in rows], dtype=float)
    returns = np.array([float(row["future_return_5d"]) for row in rows], dtype=float)
    spearman = _spearman(scores, returns)
    pearson = _pearson(scores, returns)

    low = returns[(scores >= 0.0) & (scores < 0.2)]
    high = returns[(scores >= 0.8) & (scores <= 1.0)]
    high_low_spread = float(high.mean() - low.mean()) if len(low) and len(high) else None

    result = {
        "rows": int(len(rows)),
        "spearman_ic": spearman,
        "pearson_correlation": pearson,
        "low_score_rows": int(len(low)),
        "high_score_rows": int(len(high)),
        "high_minus_low_mean_return_spread": high_low_spread,
    }

    if bootstrap and spearman is not None and len(scores) >= BLOCK_SIZE:
        boot = _bootstrap_spearman(scores, returns, seed=seed)
        if len(boot):
            ci_low, ci_high = np.quantile(boot, [0.025, 0.975])
            result.update({
                "bootstrap_replicates": int(len(boot)),
                "bootstrap_ci_95_low": float(ci_low),
                "bootstrap_ci_95_high": float(ci_high),
                "bootstrap_probability_ic_le_zero": float(np.mean(boot <= 0.0)),
            })
        else:
            result.update({
                "bootstrap_replicates": 0,
                "bootstrap_ci_95_low": None,
                "bootstrap_ci_95_high": None,
                "bootstrap_probability_ic_le_zero": None,
            })
    else:
        result.update({
            "bootstrap_replicates": 0,
            "bootstrap_ci_95_low": None,
            "bootstrap_ci_95_high": None,
            "bootstrap_probability_ic_le_zero": None,
        })
    return result


def evaluate(signal_diagnostics: list[dict], shared_artifacts: list[dict]) -> dict:
    signals = _by_symbol(signal_diagnostics)
    artifacts = _by_symbol(shared_artifacts)
    if set(signals) != set(SYMBOLS) or set(artifacts) != set(SYMBOLS):
        raise ValueError("reports must contain exactly PETR4, VALE3 and ITUB4")

    symbol_reports = []
    all_rows: list[dict] = []
    for symbol in SYMBOLS:
        rows = _paired_rows(signals[symbol], artifacts[symbol])
        folds = artifacts[symbol].get("fold_metadata")
        if not isinstance(folds, list) or len(folds) != EXPECTED_FOLDS:
            raise ValueError(f"{symbol}: expected exactly {EXPECTED_FOLDS} fold metadata entries")

        fold_reports = []
        for fold in folds:
            selected = _fold_rows(rows, fold)
            fold_reports.append({
                "fold": int(fold["fold"]),
                "test_start": str(fold["test_start"]),
                "test_end": str(fold["test_end"]),
                **_metrics(selected, bootstrap=False, seed=RANDOM_SEED + int(fold["fold"])),
            })

        symbol_reports.append({
            "symbol": symbol,
            "threshold": THRESHOLD,
            "horizon": HORIZON,
            "overall": _metrics(rows, bootstrap=False, seed=RANDOM_SEED),
            "folds": fold_reports,
        })
        all_rows.extend(rows)

    overall = _metrics(all_rows, bootstrap=True, seed=RANDOM_SEED)
    fold_ics = [
        report["spearman_ic"]
        for symbol in symbol_reports
        for report in symbol["folds"]
        if report["spearman_ic"] is not None
    ]

    return {
        "question": (
            "Does the fixed XGBoost OOS probability score have a statistically "
            "persistent relationship with future 5d returns without changing the policy?"
        ),
        "method": {
            "oos_only": True,
            "policy": "baseline_060",
            "threshold": THRESHOLD,
            "horizon": HORIZON,
            "fold_definition": "existing 500-train / 100-test / 100-step OOS folds",
            "metrics": ["Spearman rank IC", "Pearson correlation", "fixed [0.8,1.0] minus [0.0,0.2) return spread"],
            "bootstrap": "circular block bootstrap on the paired OOS score/return sequence",
            "block_size": BLOCK_SIZE,
            "replicates": BOOTSTRAP_REPLICATES,
            "seed": RANDOM_SEED,
            "selection_or_tuning": False,
            "interpretation": (
                "Descriptive predictive-ordering diagnostic. The fixed score bins and "
                "existing OOS folds are used only for diagnosis; no threshold, model, "
                "policy, or promotion decision is selected."
            ),
        },
        "symbols": symbol_reports,
        "overall": overall,
        "fold_summary": {
            "symbol_folds": int(len(fold_ics)),
            "positive_ic_folds": int(np.sum(np.array(fold_ics) > 0.0)),
            "negative_ic_folds": int(np.sum(np.array(fold_ics) < 0.0)),
            "positive_ic_fraction": float(np.mean(np.array(fold_ics) > 0.0)) if fold_ics else None,
            "mean_fold_spearman_ic": float(np.mean(fold_ics)) if fold_ics else None,
            "median_fold_spearman_ic": float(np.median(fold_ics)) if fold_ics else None,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--signal-diagnostics", default="artifacts/xgboost-oos-signal-diagnostics/report.json")
    parser.add_argument("--shared-artifact-dir", default="artifacts/xgboost-oos-shared")
    parser.add_argument("--output", default="artifacts/xgboost-oos-score-ordering-diagnosis/report.json")
    args = parser.parse_args()

    signals = json.loads(Path(args.signal_diagnostics).read_text(encoding="utf-8"))
    artifacts = [
        json.loads((Path(args.shared_artifact_dir) / f"{symbol}.json").read_text(encoding="utf-8"))
        for symbol in SYMBOLS
    ]
    report = evaluate(signals, artifacts)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
