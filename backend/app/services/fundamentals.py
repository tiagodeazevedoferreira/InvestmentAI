from __future__ import annotations

import math

from .providers import get_provider


def fundamental_metrics(symbol: str, provider: str = "openbb") -> dict:
    data = get_provider(provider).fundamentals(symbol)
    return {"symbol": symbol.upper(), "provider": provider, "raw": data}


def safe_ratio(numerator, denominator):
    if numerator is None or denominator in (None, 0):
        return None
    return float(numerator / denominator)


def invested_capital(
    equity: float | None,
    total_debt: float | None,
    cash: float | None,
) -> float | None:
    """Return invested capital as equity + interest-bearing debt - cash.

    The definition is intentionally explicit and uses point-in-time balance-sheet
    values. Missing inputs return None rather than being silently substituted.
    """
    values = (equity, total_debt, cash)
    if any(value is None for value in values):
        return None
    if any(not math.isfinite(float(value)) for value in values):
        raise ValueError("invested-capital inputs must be finite")
    capital = float(equity) + float(total_debt) - float(cash)
    if capital <= 0:
        raise ValueError("invested capital must be greater than zero")
    return capital


def roic(
    operating_income: float | None,
    tax_rate: float | None,
    equity: float | None,
    total_debt: float | None,
    cash: float | None,
) -> float | None:
    """Calculate ROIC as NOPAT / invested capital.

    NOPAT = operating income * (1 - tax rate), and invested capital is
    equity + total debt - cash. The tax rate must be supplied explicitly as an
    effective tax-rate assumption; it is not inferred from incomplete statements.
    """
    if operating_income is None or tax_rate is None:
        return None
    if not math.isfinite(float(operating_income)):
        raise ValueError("operating income must be finite")
    if not math.isfinite(float(tax_rate)) or not 0 <= float(tax_rate) <= 1:
        raise ValueError("tax rate must be finite and between 0 and 1")
    capital = invested_capital(equity, total_debt, cash)
    if capital is None:
        return None
    nopat = float(operating_income) * (1.0 - float(tax_rate))
    return nopat / capital


def derived_multiples(
    price,
    shares,
    book_value,
    net_income,
    revenue,
    ebitda,
    enterprise_value,
    dividends,
    operating_income=None,
    tax_rate=None,
    total_debt=None,
    cash=None,
):
    market_cap = price * shares if price is not None and shares is not None else None
    return {
        "pe": safe_ratio(market_cap, net_income),
        "pb": safe_ratio(market_cap, book_value),
        "ev_ebitda": safe_ratio(enterprise_value, ebitda),
        "roe": safe_ratio(net_income, book_value),
        "roic": roic(operating_income, tax_rate, book_value, total_debt, cash),
        "dividend_yield": safe_ratio(dividends, market_cap),
        "market_cap": market_cap,
        "revenue": revenue,
        "ebitda": ebitda,
        "net_income": net_income,
    }
