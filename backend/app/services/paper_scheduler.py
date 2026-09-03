from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from zoneinfo import ZoneInfo

import pandas as pd

from .paper_automation import evaluate_paper_signal
from .paper_ledger import PaperDecisionLedger
from .paper_store import PaperAccountStore
from .providers import MarketDataProvider, get_provider

B3_TZ = ZoneInfo("America/Sao_Paulo")
DEFAULT_SYMBOLS = ("PETR4", "VALE3", "ITUB4")


@dataclass(frozen=True)
class SchedulerResult:
    symbol: str
    status: str
    signal_id: str | None = None
    action: str | None = None
    bar_timestamp: str | None = None
    executed: bool = False
    order: dict | None = None
    reason: str | None = None


def yahoo_symbol(symbol: str) -> str:
    normalized = symbol.strip().upper()
    if not normalized:
        raise ValueError("symbol is required")
    return normalized if normalized.endswith(".SA") else f"{normalized}.SA"


def bar_timestamp(frame: pd.DataFrame) -> str:
    if frame.empty:
        raise ValueError("market data is empty")
    value = frame.index[-1]
    if isinstance(value, pd.Timestamp):
        value = value.to_pydatetime()
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat()
    return str(value)


def signal_id(symbol: str, timestamp: str, action: str) -> str:
    return sha256(f"{symbol.upper()}|{timestamp}|{action}".encode()).hexdigest()[:24]


def b3_session_allowed(now: datetime | None = None) -> tuple[bool, str]:
    """Guard the scheduler against weekends and non-session hours.

    The scheduler is intended for a post-close daily-bar run. Therefore the
    allowed window is 17:00–23:00 BRT on weekdays: the latest completed daily
    bar is expected after the regular B3 session has ended.
    """
    current = (now or datetime.now(timezone.utc)).astimezone(B3_TZ)
    if current.weekday() >= 5:
        return False, "B3 session guard: weekend"
    minutes = current.hour * 60 + current.minute
    if not 17 * 60 <= minutes <= 23 * 60:
        return False, "B3 session guard: outside post-close scheduler window"
    return True, "B3 session guard passed"


def run_symbol(
    provider: MarketDataProvider,
    account_store: PaperAccountStore,
    ledger: PaperDecisionLedger,
    symbol: str,
    *,
    target_allocation: float = 0.05,
    period: str = "3mo",
    execute: bool = True,
) -> SchedulerResult:
    display_symbol = symbol.strip().upper().removesuffix(".SA")
    frame = provider.history(yahoo_symbol(display_symbol), period=period)
    if frame.empty:
        raise ValueError(f"No market data for {display_symbol}")
    if not frame.index.is_monotonic_increasing:
        frame = frame.sort_index()

    timestamp = bar_timestamp(frame)
    preview = evaluate_paper_signal(
        account_store.get(),
        display_symbol,
        frame,
        max_order_notional=account_store.settings.paper_max_order_notional,
        target_allocation=target_allocation,
        execute=False,
    )
    action = preview["decision"]["action"]
    sid = signal_id(display_symbol, timestamp, action)
    created, existing = ledger.claim(
        sid,
        symbol=display_symbol,
        bar_timestamp=timestamp,
        action=action,
    )
    if not created and existing.get("status") == "completed":
        return SchedulerResult(
            symbol=display_symbol,
            status="duplicate_skipped",
            signal_id=sid,
            action=action,
            bar_timestamp=timestamp,
            executed=bool(existing.get("executed")),
            order=existing.get("order"),
            reason="decision already completed in Firebase ledger",
        )

    result = evaluate_paper_signal(
        account_store.get(),
        display_symbol,
        frame,
        max_order_notional=account_store.settings.paper_max_order_notional,
        target_allocation=target_allocation,
        execute=execute,
        client_order_id=f"paper-{sid}" if execute else None,
    )
    if result.get("executed"):
        account_store.save()
        ledger.complete(sid, executed=True, order=result.get("order"))
    elif result.get("error"):
        ledger.complete(sid, executed=False, order=None, error=result["error"])
    else:
        ledger.complete(sid, executed=False, order=None)

    decision = result["decision"]
    return SchedulerResult(
        symbol=display_symbol,
        status="executed" if result.get("executed") else "decided",
        signal_id=sid,
        action=decision["action"],
        bar_timestamp=timestamp,
        executed=bool(result.get("executed")),
        order=result.get("order"),
        reason=decision.get("reason") or result.get("error"),
    )


def run_scheduler(
    symbols: list[str] | tuple[str, ...] = DEFAULT_SYMBOLS,
    *,
    provider: MarketDataProvider | None = None,
    account_store: PaperAccountStore | None = None,
    ledger: PaperDecisionLedger | None = None,
    target_allocation: float = 0.05,
    period: str = "3mo",
    execute: bool = True,
    force: bool = False,
) -> list[SchedulerResult]:
    allowed, guard_reason = b3_session_allowed()
    if not force and not allowed:
        return [SchedulerResult(symbol="*", status="guard_skipped", reason=guard_reason)]

    store = account_store or PaperAccountStore()
    if not store.firebase.enabled:
        raise RuntimeError("Firebase must be configured for scheduled paper execution")
    decision_ledger = ledger or PaperDecisionLedger(firebase=store.firebase)
    data_provider = provider or get_provider("openbb")

    results: list[SchedulerResult] = []
    for symbol in symbols:
        try:
            results.append(
                run_symbol(
                    data_provider,
                    store,
                    decision_ledger,
                    symbol,
                    target_allocation=target_allocation,
                    period=period,
                    execute=execute,
                )
            )
        except Exception as exc:
            results.append(SchedulerResult(symbol=symbol, status="error", reason=str(exc)))
    return results
