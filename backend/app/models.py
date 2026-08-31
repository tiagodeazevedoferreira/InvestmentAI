from dataclasses import dataclass
from datetime import datetime
from typing import Literal

import pandas as pd
from pydantic import BaseModel, Field

class HealthResponse(BaseModel):
    status: str
    trading_mode: str

class BacktestRequest(BaseModel):
    symbol: str
    period: str = "5y"
    initial_cash: float = Field(default=10000, gt=0)

class BacktestResponse(BaseModel):
    symbol: str
    initial_cash: float
    final_equity: float
    return_pct: float
    trades: int

class PortfolioRequest(BaseModel):
    symbols: list[str] = Field(min_length=2, max_length=5)
    period: str = "2y"
    risk_free_rate: float = 0.0

class PortfolioResponse(BaseModel):
    weights: dict[str, float]
    expected_return: float
    volatility: float
    sharpe: float

class VaRRequest(BaseModel):
    weights: dict[str, float]
    period: str = "1y"
    confidence: float = Field(default=0.95, gt=0.5, lt=1.0)
    portfolio_value: float = Field(default=10000, gt=0)

class VaRResponse(BaseModel):
    confidence: float
    daily_var: float
    daily_var_pct: float

@dataclass(frozen=True)
class Signal:
    symbol: str
    action: Literal["BUY", "HOLD", "SELL"]
    reason: str
    timestamp: datetime

class FundamentalMetrics(BaseModel):
    price: float | None = None
    market_cap: float | None = None
    revenue: float | None = None
    net_income: float | None = None
    ebitda: float | None = None
    book_value: float | None = None
    enterprise_value: float | None = None
    dividends_per_share: float | None = None
    shares_outstanding: float | None = None
    pe: float | None = None
    pb: float | None = None
    ev_ebitda: float | None = None
    roe: float | None = None
    roic: float | None = None
    dividend_yield: float | None = None

class ValuationRequest(BaseModel):
    dividend_per_share: float = Field(gt=0)
    growth_rate: float
    required_return: float

class ValuationResponse(BaseModel):
    fair_value: float
    method: str

class PredictionResponse(BaseModel):
    symbol: str
    horizon_days: int
    probability_up: float | None
    model: str
    status: str
