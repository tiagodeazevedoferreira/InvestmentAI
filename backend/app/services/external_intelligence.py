from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class Direction(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    NEUTRAL = "NEUTRAL"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ExternalSignal:
    symbol: str
    timestamp: datetime
    direction: Direction = Direction.UNKNOWN
    confidence: float | None = None
    entry: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    support: float | None = None
    resistance: float | None = None
    sentiment: float | None = None
    source: str = "unknown"
    source_version: str | None = None
    raw_reference: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.symbol:
            raise ValueError("symbol is required")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if self.sentiment is not None and not -1 <= self.sentiment <= 1:
            raise ValueError("sentiment must be between -1 and 1")


@dataclass(frozen=True)
class FusedSignal:
    symbol: str
    direction: Direction
    score: float
    confidence: float
    sources: tuple[str, ...]
    blocked: bool
    reasons: tuple[str, ...]


class SignalFusion:
    def __init__(self, weights: dict[str, float] | None = None, min_confidence: float = 0.60) -> None:
        self.weights = weights or {}
        self.min_confidence = min_confidence

    def fuse(self, signals: list[ExternalSignal]) -> FusedSignal:
        if not signals:
            raise ValueError("at least one signal is required")
        symbol = signals[0].symbol
        if any(s.symbol != symbol for s in signals):
            raise ValueError("all signals must reference the same symbol")
        total = 0.0
        weight_sum = 0.0
        for signal in signals:
            w = self.weights.get(signal.source, 1.0)
            c = signal.confidence or 0.0
            total += (c if signal.direction is Direction.LONG else -c if signal.direction is Direction.SHORT else 0.0) * w
            weight_sum += w
        score = total / weight_sum if weight_sum else 0.0
        direction = Direction.LONG if score > 0 else Direction.SHORT if score < 0 else Direction.NEUTRAL
        confidence = abs(score)
        reasons = []
        if confidence < self.min_confidence:
            reasons.append("fused confidence below threshold")
        return FusedSignal(symbol, direction, score, confidence, tuple(sorted({s.source for s in signals})), bool(reasons), tuple(reasons))


class RiskGate:
    def __init__(self, min_confidence: float = 0.60, min_sources: int = 2, max_age_seconds: int = 900) -> None:
        self.min_confidence = min_confidence
        self.min_sources = min_sources
        self.max_age_seconds = max_age_seconds

    def evaluate(self, signal: FusedSignal, *, signal_age_seconds: float | None = None, environment: str = "paper") -> tuple[bool, tuple[str, ...]]:
        reasons = list(signal.reasons)
        if signal.direction in {Direction.NEUTRAL, Direction.UNKNOWN}:
            reasons.append("no actionable direction")
        if signal.confidence < self.min_confidence:
            reasons.append("confidence threshold not met")
        if len(signal.sources) < self.min_sources:
            reasons.append("independent evidence threshold not met")
        if signal_age_seconds is not None and signal_age_seconds > self.max_age_seconds:
            reasons.append("signal is stale")
        if environment == "live":
            reasons.append("live execution remains disabled in phases 1-9")
        return not reasons, tuple(dict.fromkeys(reasons))


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
