from __future__ import annotations

from scripts.run_xgboost_oos_score_bucket_diagnosis import evaluate


def _signal(symbol: str) -> dict:
    observations = []
    for index in range(100):
        observations.append(
            {
                "timestamp": f"2026-01-{index + 1:03d}T00:00:00+00:00",
                "future_return_5d": -0.01 + (index // 20) * 0.01,
            }
        )
    return {"symbol": symbol, "conditional_return_observations_5d": observations}


def _artifact(symbol: str) -> dict:
    probabilities = [0.1, 0.3, 0.5, 0.7, 0.9]
    predictions = []
    for index in range(100):
        predictions.append(
            {
                "timestamp": f"2026-01-{index + 1:03d}T00:00:00+00:00",
                "probability": probabilities[index // 20],
            }
        )
    return {"symbol": symbol, "predictions": predictions}


def test_score_bucket_diagnosis_is_deterministic_and_fixed() -> None:
    symbols = ("PETR4", "VALE3", "ITUB4")
    report = evaluate(
        [_signal(symbol) for symbol in symbols],
        [_artifact(symbol) for symbol in symbols],
    )

    assert report["overall"]["rows"] == 300
    assert report["overall"]["monotonicity"]["adjacent_non_decreasing_count"] == 4
    assert report["overall"]["monotonicity"]["strictly_monotonic_increasing"] is True
    assert [row["rows"] for row in report["overall"]["bins"]] == [60, 60, 60, 60, 60]


def test_score_bucket_requires_matching_oos_timestamps() -> None:
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
