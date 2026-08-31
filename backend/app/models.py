from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, field_validator

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

    @field_validator("symbols")
    @classmethod
    def unique_symbols(cls, v):
        normalized = [s.strip().upper() for s in v if s.strip()]
        if len(set(normalized)) != len(normalized):
            raise ValueError("symbols must be unique")
        return normalized

class PortfolioResponse(BaseModel):
    weights: dict[str, float]
    expected_return: float
    volatility: float
    sharpe: float
    frontier: list[dict] = []

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

class FundamentalResponse(BaseModel):
    symbol: str
    provider: str
    data: dict

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
