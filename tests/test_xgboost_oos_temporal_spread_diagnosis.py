from __future__ import annotations

from scripts.run_xgboost_oos_temporal_spread_diagnosis import evaluate


def _signal(symbol: str) -> dict:
    observations = []
    for fold in range(7):
        day = fold + 1
        for offset in range(100):
            observations.append(
                {
                    "timestamp": f"2026-01-{day:02d}T00:00:00+00:00",
                    "regime": "long" if offset < 50 else "cash",
                    "future_return_5d": 0.02 if offset < 50 else 0.01,
                }
            )
    return {
        "symbol": symbol,
        "conditional_return_observations_5d": observations,
    }


def _artifact(symbol: str) -> dict:
    folds = []
    for fold in range(7):
        day = fold + 1
        folds.append(
            {
                "fold": fold + 1,
                "train_start": "2024-01-01T00:00:00+00:00",
                "train_end": "2025-12-31T00:00:00+00:00",
                "test_start": f"2026-01-{day:02d}T00:00:00+00:00",
                "test_end": f"2026-01-{day:02d}T00:00:00+00:00",
            }
        )
    return {"symbol": symbol, "fold_metadata": folds}


def test_temporal_diagnosis_is_deterministic_and_uses_existing_folds() -> None:
    symbols = ("PETR4", "VALE3", "ITUB4")
    signals = [_signal(symbol) for symbol in symbols]
    artifacts = [_artifact(symbol) for symbol in symbols]

    report = evaluate(signals, artifacts)

    assert report["summary"]["total_symbol_folds"] == 21
    assert report["summary"]["positive_spread_folds"] == 21
    assert report["summary"]["negative_spread_folds"] == 0
    assert report["summary"]["all_symbol_folds_positive"] is True
    assert all(
        symbol["summary"]["positive_spread_folds"] == 7
        for symbol in report["symbols"]
    )


def test_temporal_diagnosis_requires_all_symbols() -> None:
    signals = [_signal(symbol) for symbol in ("PETR4", "VALE3", "ITUB4")]
    artifacts = [_artifact(symbol) for symbol in ("PETR4", "VALE3")]

    try:
        evaluate(signals, artifacts)
    except ValueError as exc:
        assert "exactly PETR4, VALE3 and ITUB4" in str(exc)
    else:
        raise AssertionError("expected symbol coverage failure")
