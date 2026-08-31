from __future__ import annotations
from .providers import get_provider


def fundamental_metrics(symbol: str, provider: str = "openbb") -> dict:
    data = get_provider(provider).fundamentals(symbol)
    return {"symbol": symbol.upper(), "provider": provider, "raw": data}


def safe_ratio(numerator, denominator):
    if numerator is None or denominator in (None, 0):
        return None
    return float(numerator / denominator)


def derived_multiples(price, shares, book_value, net_income, revenue, ebitda, enterprise_value, dividends):
    market_cap = price * shares if price is not None and shares is not None else None
    return {
        "pe": safe_ratio(market_cap, net_income),
        "pb": safe_ratio(market_cap, book_value),
        "ev_ebitda": safe_ratio(enterprise_value, ebitda),
        "roe": safe_ratio(net_income, book_value),
        "roic": None,
        "dividend_yield": safe_ratio(dividends, market_cap),
        "market_cap": market_cap,
        "revenue": revenue,
        "ebitda": ebitda,
        "net_income": net_income,
    }
