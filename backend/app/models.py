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

class TradingViewWebhook(BaseModel):
    """Normalized payload emitted by the InvestmentAI Pine validator."""
    source: Literal["tradingview"] = "tradingview"
    symbol: str = Field(min_length=1, max_length=32)
    exchange: str = Field(min_length=1, max_length=64)
    timeframe: str = Field(min_length=1, max_length=16)
    bar_time: datetime
    close: float
    ema_fast: float
    ema_slow: float
    rsi14: float = Field(ge=0, le=100)
    bb_upper: float
    bb_basis: float
    bb_lower: float
    volume: float = Field(ge=0)
    ema_state: Literal["bullish", "bearish", "neutral"] | None = None
    rsi_state: Literal["oversold", "neutral", "overbought"] | None = None
    bb_state: Literal["below_lower", "inside", "above_upper"] | None = None
    bar_confirmed: bool = True
    received_at: datetime | None = None

    @field_validator("symbol", "exchange", "timeframe")
    @classmethod
    def normalize_labels(cls, value: str) -> str:
        return value.strip().upper()

class TradingViewWebhookResponse(BaseModel):
    accepted: bool
    source: str
    symbol: str
    timeframe: str
    event_id: str
    received_at: datetime

class PaperOrderRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=32)
    side: Literal["BUY", "SELL"]
    quantity: int = Field(gt=0, le=100000)
    reference_price: float = Field(gt=0)
    order_type: Literal["MARKET", "LIMIT"] = "MARKET"
    limit_price: float | None = Field(default=None, gt=0)
    reason: str | None = Field(default=None, max_length=500)

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return value.strip().upper()

class PaperMarkRequest(BaseModel):
    prices: dict[str, float]

    @field_validator("prices")
    @classmethod
    def validate_prices(cls, value: dict[str, float]) -> dict[str, float]:
        if not value:
            raise ValueError("prices cannot be empty")
        normalized = {}
        for key, price in value.items():
            if price <= 0:
                raise ValueError(f"price must be positive for {key}")
            normalized[key.strip().upper()] = price
        return normalized

class PaperResetRequest(BaseModel):
    initial_cash: float = Field(default=100_000, gt=0)

class PaperAccountResponse(BaseModel):
    environment: str
    initial_cash: float
    cash: float
    market_value: float
    equity: float
    realized_pnl: float
    unrealized_pnl: float
    positions: dict[str, dict]
    open_orders: list[dict]
    orders_count: int
    executions_count: int

class PaperAutomationRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=32)
    bars: list[dict[str, float]] = Field(min_length=25, max_length=5000)
    execute: bool = True
    target_allocation: float = Field(default=0.05, gt=0, le=1)

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return value.strip().upper()

class PaperAutomationResponse(BaseModel):
    decision: dict
    executed: bool
    order: dict | None = None
    error: str | None = None
