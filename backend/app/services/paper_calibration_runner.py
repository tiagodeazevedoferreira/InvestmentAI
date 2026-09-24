from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .paper_calibration import build_calibration_report
from .paper_ledger import PaperDecisionLedger
from .paper_outcomes import OutcomeObservation, attribute_decision
from .providers import MarketDataProvider


@dataclass(frozen=True)
class PaperCalibrationRunResult:
    decisions_seen: int
    decisions_processed: int
    outcomes_persisted: int
    completed_observations: int
    incomplete_observations: int
    report: dict


def calibrate_persisted_paper_outcomes(
    ledger: PaperDecisionLedger,
    provider: MarketDataProvider,
    *,
    symbol: str | None = None,
    limit: int = 200,
    period: str = "5y",
    horizons: Iterable[int] = (1, 5, 20),
    transaction_cost_bps: float = 0.0,
) -> PaperCalibrationRunResult:
    """Attribute persisted PAPER decisions and build a descriptive report.

    This function never submits or modifies orders. It only reads decisions,
    reads historical market data and writes outcome metadata to the same ledger.
    """
    requested_horizons = tuple(int(value) for value in horizons)
    if not requested_horizons or any(value <= 0 for value in requested_horizons):
        raise ValueError("horizons must contain positive integers")
    if limit <= 0:
        raise ValueError("limit must be positive")

    records = ledger.list_records(symbol=symbol, limit=limit)
    observations: list[OutcomeObservation] = []
    processed = 0
    persisted = 0
    incomplete = 0
    for record in records:
        if not record.get("signal_id") or not record.get("bar_timestamp") or not record.get("decision_price"):
            raise ValueError("paper ledger record is missing causal decision provenance")
        frame = provider.history(str(record["symbol"]).upper(), period=period)
        if frame.empty:
            raise ValueError(f"no market data for {record['symbol']}")
        if not frame.index.is_monotonic_increasing:
            frame = frame.sort_index()
        attributed = attribute_decision(
            {
                "signal_id": record["signal_id"],
                "symbol": record["symbol"],
                "action": record["action"],
                "bar_timestamp": record["bar_timestamp"],
                "price": record["decision_price"],
            },
            frame,
            horizons=requested_horizons,
        )
        ledger.save_outcomes(str(record["signal_id"]), attributed)
        processed += 1
        persisted += len(attributed)
        incomplete += sum(1 for item in attributed if item.signed_return is None)
        observations.extend(attributed)

    report = build_calibration_report(observations, transaction_cost_bps=transaction_cost_bps)
    return PaperCalibrationRunResult(
        decisions_seen=len(records),
        decisions_processed=processed,
        outcomes_persisted=persisted,
        completed_observations=sum(1 for item in observations if item.signed_return is not None),
        incomplete_observations=incomplete,
        report=report,
    )
