def gordon_growth_value(dividend_per_share: float, growth_rate: float, required_return: float) -> float:
    if dividend_per_share <= 0:
        raise ValueError("Dividend must be positive")
    if required_return <= growth_rate:
        raise ValueError("Required return must exceed growth rate")
    return dividend_per_share * (1 + growth_rate) / (required_return - growth_rate)

def dcf_value(cash_flows: list[float], discount_rate: float, terminal_growth: float) -> float:
    if not cash_flows or discount_rate <= terminal_growth or discount_rate <= -1:
        raise ValueError("Invalid DCF assumptions")
    pv = sum(cf / ((1 + discount_rate) ** (i + 1)) for i, cf in enumerate(cash_flows))
    terminal = cash_flows[-1] * (1 + terminal_growth) / (discount_rate - terminal_growth)
    return pv + terminal / ((1 + discount_rate) ** len(cash_flows))

def safe_ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator

def fundamental_metrics(price=None, market_cap=None, revenue=None, net_income=None, ebitda=None,
                        book_value=None, enterprise_value=None, dividends_per_share=None,
                        shares_outstanding=None):
    return {
        "price": price, "market_cap": market_cap, "revenue": revenue, "net_income": net_income,
        "ebitda": ebitda, "book_value": book_value, "enterprise_value": enterprise_value,
        "dividends_per_share": dividends_per_share, "shares_outstanding": shares_outstanding,
        "pe": safe_ratio(market_cap, net_income),
        "pb": safe_ratio(market_cap, book_value),
        "ev_ebitda": safe_ratio(enterprise_value, ebitda),
        "roe": safe_ratio(net_income, book_value),
        "roic": None,
        "dividend_yield": safe_ratio(dividends_per_share, price),
    }
