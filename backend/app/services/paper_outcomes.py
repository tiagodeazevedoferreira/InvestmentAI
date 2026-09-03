from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

import pandas as pd


@dataclass(frozen=True)
class OutcomeObservation:
    signal_id: str
    symbol: str
    action: str
    bar_timestamp: str
    decision_price: float
    horizon_bars: int
    outcome_timestamp: str | None
    outcome_price: float | None
    forward_return: float | None
    signed_return: float | None
    hit: bool | None


def _normalized_close(frame: pd.DataFrame) -> pd.Series:
    if "Close" not in frame.columns:
        raise ValueError("market data must contain Close")
    close = pd.to_numeric(frame["Close"], errors="coerce").dropna()
    if close.empty:
        raise ValueError("market data contains no valid Close values")
    return close


def _position_for_timestamp(index: pd.Index, timestamp: str) -> int:
    target = pd.Timestamp(timestamp)
    if target.tzinfo is None:
        target = target.tz_localize("UTC")
    else:
        target = target.tz_convert("UTC")

    normalized = pd.DatetimeIndex(index)
    if normalized.tz is None:
        normalized = normalized.tz_localize("UTC")
    else:
        normalized = normalized.tz_convert("UTC")

    matches = normalized == target
    if not matches.any():
        raise ValueError(f"decision timestamp not found in market data: {timestamp}")
    return int(matches.argmax())


def attribute_decision(
    decision: Mapping,
    frame: pd.DataFrame,
    *,
    horizons: Iterable[int] = (1, 5, 20),
) -> list[OutcomeObservation]:
    """Attribute forward price outcomes to a paper decision.

    BUY is considered successful when the forward return is positive; SELL is
    successful when it is negative. HOLD is retained as an unsigned market
    observation and has no hit classification. Only completed horizons are
    emitted with a price; insufficient future bars remain explicitly pending.
    """
    close = _normalized_close(frame)
    action = str(decision.get("action", "")).upper()
    if action not in {"BUY", "SELL", "HOLD"}:
        raise ValueError("decision action must be BUY, SELL or HOLD")
    signal_id = str(decision.get("signal_id", ""))
    if not signal_id:
        raise ValueError("decision signal_id is required")
    timestamp = str(decision.get("bar_timestamp", ""))
    if not timestamp:
        raise ValueError("decision bar_timestamp is required")
    decision_price = float(decision.get("price", close.iloc[-1]))
    if decision_price <= 0:
        raise ValueError("decision price must be positive")

    position = _position_for_timestamp(close.index, timestamp)
    result: list[OutcomeObservation] = []
    for raw_horizon in horizons:
        horizon = int(raw_horizon)
        if horizon <= 0:
            raise ValueError("horizons must contain positive integers")
        target_position = position + horizon
        if target_position >= len(close):
            result.append(
                OutcomeObservation(
                    signal_id, str(decision.get("symbol", "")).upper(), action,
                    timestamp, decision_price, horizon, None, None, None, None, None,
                )
            )
            continue

        outcome_price = float(close.iloc[target_position])
        forward_return = outcome_price / decision_price - 1.0
        signed_return = forward_return if action == "BUY" else -forward_return if action == "SELL" else forward_return
        hit = signed_return > 0 if action in {"BUY", "SELL"} else None
        result.append(
            OutcomeObservation(
                signal_id, str(decision.get("symbol", "")).upper(), action,
                timestamp, decision_price, horizon,
                pd.Timestamp(close.index[target_position]).isoformat(),
                outcome_price, forward_return, signed_return, hit,
            )
        )
    return result


def summarize_outcomes(observations: Iterable[OutcomeObservation]) -> dict:
    """Aggregate completed observations by action and horizon."""
    rows = [item for item in observations if item.signed_return is not None]
    summary: dict[str, dict] = {}
    for item in rows:
        key = f"{item.action}:{item.horizon_bars}"
        bucket = summary.setdefault(key, {"action": item.action, "horizon_bars": item.horizon_bars, "observations": 0, "hits": 0, "hit_rate": None, "mean_signed_return": None, "median_signed_return": None})
        bucket["observations"] += 1
        if item.hit:
            bucket["hits"] += 1
        values = bucket.setdefault("_values", [])
        values.append(item.signed_return)

    for bucket in summary.values():
        values = bucket.pop("_values")
        bucket["hit_rate"] = bucket["hits"] / bucket["observations"] if bucket["observations"] else None
        bucket["mean_signed_return"] = sum(values) / len(values) if values else None
        bucket["median_signed_return"] = float(pd.Series(values).median()) if values else None
    return {"observations": len(rows), "groups": list(summary.values())}
