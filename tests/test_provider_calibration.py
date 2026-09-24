import pytest

from backend.app.services.provider_calibration import (
    ProviderOutcomeObservation,
    build_provider_calibration,
)


def observation(provider, confidence, hit, signed_return, horizon=5):
    return ProviderOutcomeObservation(
        provider=provider,
        symbol="PETR4",
        horizon_bars=horizon,
        confidence=confidence,
        hit=hit,
        signed_return=signed_return,
        timestamp="2026-09-01T20:00:00+00:00",
    )


def test_provider_calibration_is_grouped_deterministically():
    report = build_provider_calibration([
        observation("TradingView", 0.8, True, 0.02),
        observation("TradingView", 0.4, False, -0.01),
        observation("Doto", 0.9, True, 0.03),
    ])

    assert report["providers"] == ["doto", "tradingview"]
    assert report["observations"] == 3
    assert [(g["provider"], g["horizon_bars"]) for g in report["groups"]] == [
        ("doto", 5),
        ("tradingview", 5),
    ]


def test_provider_calibration_metrics():
    report = build_provider_calibration([
        observation("model", 0.8, True, 0.02),
        observation("model", 0.6, False, -0.01),
    ])
    group = report["groups"][0]

    assert group["observations"] == 2
    assert group["hits"] == 1
    assert group["hit_rate"] == pytest.approx(0.5)
    assert group["mean_confidence"] == pytest.approx(0.7)
    assert group["brier_score"] == pytest.approx(0.20)
    assert group["calibration_gap"] == pytest.approx(0.20)
    assert group["mean_signed_return"] == pytest.approx(0.005)


def test_invalid_observation_fails_closed():
    with pytest.raises(ValueError):
        observation("model", 1.1, True, 0.01)

    with pytest.raises(ValueError):
        ProviderOutcomeObservation(
            provider="model",
            symbol="PETR4",
            horizon_bars=5,
            confidence=0.5,
            hit=True,
            signed_return=float("nan"),
            timestamp="2026-09-01T20:00:00+00:00",
        )


def test_empty_calibration_fails_closed():
    with pytest.raises(ValueError):
        build_provider_calibration([])
