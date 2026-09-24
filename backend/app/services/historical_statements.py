from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable, Mapping


@dataclass(frozen=True)
class NormalizedStatement:
    symbol: str
    period_end: str
    statement_type: str
    revenue: float | None = None
    operating_income: float | None = None
    net_income: float | None = None
    ebitda: float | None = None
    total_assets: float | None = None
    total_debt: float | None = None
    cash: float | None = None
    equity: float | None = None
    operating_cash_flow: float | None = None
    capex: float | None = None

    def __post_init__(self) -> None:
        if not self.symbol.strip():
            raise ValueError("symbol is required")
        if not self.period_end.strip():
            raise ValueError("period_end is required")
        if not self.statement_type.strip():
            raise ValueError("statement_type is required")
        for name in (
            "revenue", "operating_income", "net_income", "ebitda",
            "total_assets", "total_debt", "cash", "equity",
            "operating_cash_flow", "capex",
        ):
            value = getattr(self, name)
            if value is not None and not isfinite(float(value)):
                raise ValueError(f"{name} must be finite")


_FIELD_ALIASES = {
    "revenue": ("revenue", "totalrevenue", "total_revenue"),
    "operating_income": ("operating_income", "operatingincome"),
    "net_income": ("net_income", "netincome", "netIncomeToCommon"),
    "ebitda": ("ebitda",),
    "total_assets": ("total_assets", "totalassets"),
    "total_debt": ("total_debt", "totaldebt"),
    "cash": ("cash", "cash_and_equivalents", "cashandcashequivalents"),
    "equity": ("equity", "total_equity", "totalstockholderequity"),
    "operating_cash_flow": ("operating_cash_flow", "operatingcashflow"),
    "capex": ("capex", "capital_expenditure", "capitalexpenditure"),
}


def _normalized_keys(record: Mapping[str, object]) -> dict[str, object]:
    return {str(key).replace("-", "").replace("_", "").lower(): value for key, value in record.items()}


def _value(record: Mapping[str, object], aliases: tuple[str, ...]) -> float | None:
    normalized = _normalized_keys(record)
    for key in aliases:
        normalized_key = key.replace("-", "").replace("_", "").lower()
        if normalized_key in normalized and normalized[normalized_key] is not None:
            value = float(normalized[normalized_key])
            if not isfinite(value):
                raise ValueError(f"{normalized_key} must be finite")
            return value
    return None


def normalize_historical_statements(
    records: Iterable[Mapping[str, object]],
    *,
    symbol: str,
    statement_type: str,
) -> tuple[NormalizedStatement, ...]:
    normalized_symbol = symbol.strip().upper().removesuffix(".SA")
    if not normalized_symbol:
        raise ValueError("symbol is required")
    if not statement_type.strip():
        raise ValueError("statement_type is required")

    output: list[NormalizedStatement] = []
    for record in records:
        if not isinstance(record, Mapping):
            raise ValueError("statement record must be a mapping")
        normalized = _normalized_keys(record)
        period_end = str(
            normalized.get("periodend")
            or normalized.get("date")
            or normalized.get("asofdate")
            or ""
        ).strip()
        if not period_end:
            raise ValueError("statement period_end is required")
        output.append(
            NormalizedStatement(
                symbol=normalized_symbol,
                period_end=period_end,
                statement_type=statement_type.strip().lower(),
                revenue=_value(record, _FIELD_ALIASES["revenue"]),
                operating_income=_value(record, _FIELD_ALIASES["operating_income"]),
                net_income=_value(record, _FIELD_ALIASES["net_income"]),
                ebitda=_value(record, _FIELD_ALIASES["ebitda"]),
                total_assets=_value(record, _FIELD_ALIASES["total_assets"]),
                total_debt=_value(record, _FIELD_ALIASES["total_debt"]),
                cash=_value(record, _FIELD_ALIASES["cash"]),
                equity=_value(record, _FIELD_ALIASES["equity"]),
                operating_cash_flow=_value(record, _FIELD_ALIASES["operating_cash_flow"]),
                capex=_value(record, _FIELD_ALIASES["capex"]),
            )
        )
    return tuple(sorted(output, key=lambda item: item.period_end))
