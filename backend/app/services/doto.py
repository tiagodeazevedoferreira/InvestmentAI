from __future__ import annotations

from typing import Any

from .external_intelligence import Direction, ExternalSignal, utc_now


class DotoSignalAdapter:
    """Normalize observed Doto AI Market Insights into InvestmentAI evidence.

    No browser scraping or credential automation is performed here. The adapter
    is intentionally ready for an approved API/export/bridge when available.
    """
    source = "doto_ai"

    @staticmethod
    def _direction(value: Any) -> Direction:
        value = str(value or "").strip().upper()
        return {
            "BUY": Direction.LONG,
            "BULLISH": Direction.LONG,
            "LONG": Direction.LONG,
            "SELL": Direction.SHORT,
            "BEARISH": Direction.SHORT,
            "SHORT": Direction.SHORT,
            "HOLD": Direction.NEUTRAL,
            "NEUTRAL": Direction.NEUTRAL,
        }.get(value, Direction.UNKNOWN)

    @staticmethod
    def _num(payload: dict[str, Any], *keys: str) -> float | None:
        for key in keys:
            if payload.get(key) is not None:
                try:
                    return float(payload[key])
                except (TypeError, ValueError):
                    pass
        return None

    def normalize(self, payload: dict[str, Any], symbol: str) -> ExternalSignal:
        confidence = self._num(payload, "confidence", "confidence_score")
        if confidence is not None and confidence > 1:
            confidence /= 100
        return ExternalSignal(
            symbol=symbol.upper(),
            timestamp=utc_now(),
            direction=self._direction(payload.get("direction", payload.get("signal"))),
            confidence=confidence,
            entry=self._num(payload, "entry", "entry_price"),
            stop_loss=self._num(payload, "stop_loss", "stopLoss", "sl"),
            take_profit=self._num(payload, "take_profit", "takeProfit", "tp", "target"),
            support=self._num(payload, "support", "support_level"),
            resistance=self._num(payload, "resistance", "resistance_level"),
            sentiment=self._num(payload, "sentiment", "sentiment_score"),
            source=self.source,
            source_version=str(payload.get("version")) if payload.get("version") is not None else None,
            raw_reference=str(payload.get("id")) if payload.get("id") is not None else None,
            metadata={"provider_payload_keys": sorted(payload.keys())},
        )
