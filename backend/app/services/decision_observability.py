from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from .external_intelligence import Direction, FusedSignal


@dataclass(frozen=True)
class DecisionEvidence:
    source: str
    direction: str
    confidence: float
    reference: str | None = None


@dataclass(frozen=True)
class DecisionRecord:
    decision_id: str
    symbol: str
    timestamp: str
    direction: str
    score: float
    confidence: float
    allowed: bool
    environment: str
    sources: tuple[DecisionEvidence, ...]
    risk_reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_decision_record(
    *,
    decision_id: str,
    symbol: str,
    fused: FusedSignal,
    allowed: bool,
    environment: str,
    risk_reasons: tuple[str, ...] = (),
    evidence: tuple[DecisionEvidence, ...] = (),
    timestamp: datetime | None = None,
) -> DecisionRecord:
    """Create an immutable, serializable audit record of a decision.

    This is observability only: it has no broker or execution dependency.
    """
    ts = timestamp or datetime.now(timezone.utc)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return DecisionRecord(
        decision_id=decision_id,
        symbol=symbol,
        timestamp=ts.astimezone(timezone.utc).isoformat(),
        direction=fused.direction.value,
        score=fused.score,
        confidence=fused.confidence,
        allowed=allowed,
        environment=environment,
        sources=evidence,
        risk_reasons=risk_reasons,
    )
