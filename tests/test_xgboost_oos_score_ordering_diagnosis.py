from __future__ import annotations

from datetime import datetime, timedelta

from scripts.run_xgboost_oos_score_ordering_diagnosis import evaluate


def _signal(symbol: str) -> dict:
    observations = []
    start = datetime(2026, 1, 1)
    for index in range(100):
        timestamp = (start + timedelta(days=index)).isoformat() + "+00:00"
        observations.append(
            {
                "timestamp": timestamp,
                "future_return_5d": -0.01 + (index // 20) * 0.01,
            }
        )
    return {"symbol": symbol, "conditional_return_observations_5d": observations}


def _artifact(symbol: str) -> dict:
    scores = [0.1, 0.3, 0.5, 0.7, 0.9]
    predictions = []
    start = datetime(2026, 1, 1)
    for index in range(100):
        timestamp = (start + timedelta(days=index)).isoformat() + "+00:00"
        predictions.append(
            {
                "timestamp": timestamp,
                "probability": scores[index // 20],
            }
        )
    return {
        "symbol": symbol,
        "predictions": predictions,
        "fold_metadata": [
            {
                "fold": 1,
                "test_start": "2026-01-01T00:00:00+00:00",
                "test_end": "2026-04-10T00:00:00+00:00",
            }
        ],
    }


def test_score_ordering_is_deterministic_and_fixed() -> None:
    symbols = ("PETR4", "VALE3", "ITUB4")
    signals = [_signal(symbol) for symbol in symbols]
    artifacts = [_artifact(symbol) for symbol in symbols]

    # Expand the same deterministic test window to the expected seven-fold contract.
    for artifact in artifacts:
        artifact["fold_metadata"] = [
            {
                "fold": fold,
                "test_start": "2026-01-001T00:00:00+00:00",
                "test_end": "2026-01-100T00:00:00+00:00",
            }
            for fold in range(1, 8)
        ]

    first = evaluate(signals, artifacts)
    second = evaluate(signals, artifacts)

    assert first == second
    assert first["overall"]["spearman_ic"] > 0.9
    assert first["fold_summary"]["positive_ic_folds"] == 21
    assert first["overall"]["high_minus_low_mean_return_spread"] > 0.0
    assert first["overall"]["bootstrap_ci_95_low"] > 0.0


def test_score_ordering_requires_timestamp_coverage() -> None:
    signal = _signal("PETR4")
    artifact = _artifact("PETR4")
    artifact["predictions"][0]["timestamp"] = "2027-01-01T00:00:00+00:00"

    try:
        evaluate(
            [signal, _signal("VALE3"), _signal("ITUB4")],
            [artifact, _artifact("VALE3"), _artifact("ITUB4")],
        )
    except ValueError as exc:
        assert "missing future return for prediction timestamp" in str(exc)
    else:
        raise AssertionError("expected timestamp coverage failure")
