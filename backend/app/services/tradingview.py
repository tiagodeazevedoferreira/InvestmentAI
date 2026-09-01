from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from hmac import compare_digest
from typing import Any

from ..models import TradingViewWebhook


def verify_webhook_secret(provided: str | None, expected: str | None) -> bool:
    if not expected or not provided:
        return False
    return compare_digest(provided, expected)


def normalize_tradingview_payload(payload: dict[str, Any]) -> TradingViewWebhook:
    """Validate and normalize a TradingView Pine webhook payload."""
    return TradingViewWebhook.model_validate(payload)


def event_fingerprint(event: TradingViewWebhook) -> str:
    """Create a stable idempotency key for a TradingView event."""
    raw = "|".join(
        [
            event.symbol,
            event.exchange,
            event.timeframe,
            event.bar_time.isoformat(),
            str(event.close),
            str(event.ema_fast),
            str(event.ema_slow),
            str(event.rsi14),
            str(event.bb_upper),
            str(event.bb_basis),
            str(event.bb_lower),
            str(event.volume),
        ]
    )
    return sha256(raw.encode("utf-8")).hexdigest()


def normalize_timestamp(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
