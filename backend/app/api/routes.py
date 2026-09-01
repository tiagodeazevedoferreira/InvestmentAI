from fastapi import APIRouter, Header, HTTPException, Query
import pandas as pd
from ..models import HealthResponse, BacktestRequest, BacktestResponse, ValuationRequest, ValuationResponse, PortfolioRequest, PortfolioResponse, VaRRequest, VaRResponse, PredictionResponse, FundamentalResponse, TradingViewWebhook, TradingViewWebhookResponse
from ..settings import get_settings
from ..services.market_data import download_history
from ..services.providers import get_provider
from ..services.technical import indicators
from ..services.backtest import rsi_backtest
from ..services.valuation import gordon_growth_value
from ..services.portfolio import optimize_max_sharpe, efficient_frontier, parametric_var
from ..services.features import build_features
from ..services.evaluation import trading_metrics
from ..services.fundamentals import fundamental_metrics
from ..services.tradingview import event_fingerprint, normalize_timestamp, normalize_tradingview_payload, verify_webhook_secret

router = APIRouter()
settings = get_settings()

@router.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok", "trading_mode": settings.trading_mode.value}

@router.get("/market/{symbol}")
def market(symbol: str, period: str = "1y", provider: str = Query("yahoo")):
    try:
        df = get_provider(provider).history(symbol, period) if provider != "yahoo" else download_history(symbol, period)
        df = indicators(df)
        row = df.iloc[-1]
        return {"symbol": symbol.upper(), "close": float(row["Close"]), "ema9": float(row["EMA9"]), "ema21": float(row["EMA21"]), "rsi14": None if pd.isna(row["RSI14"]) else float(row["RSI14"]), "provider": provider}
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(422, str(exc)) from exc

@router.post("/integrations/tradingview/webhook", response_model=TradingViewWebhookResponse)
def tradingview_webhook(payload: dict, x_tradingview_secret: str | None = Header(default=None)):
    """Receive read-only TradingView/Pine validation events.

    This endpoint records no orders and cannot change trading mode. A shared
    secret is mandatory so an unconfigured deployment fails closed.
    """
    if not settings.tradingview_webhook_secret:
        raise HTTPException(503, "TradingView webhook is not configured")
    if not verify_webhook_secret(x_tradingview_secret, settings.tradingview_webhook_secret):
        raise HTTPException(401, "Invalid TradingView webhook secret")
    try:
        event = normalize_tradingview_payload(payload)
    except ValueError as exc:
        raise HTTPException(422, "Invalid TradingView payload") from exc

    received_at = normalize_timestamp(event.received_at)
    event_id = event_fingerprint(event)
    return {
        "accepted": True,
        "source": event.source,
        "symbol": event.symbol,
        "timeframe": event.timeframe,
        "event_id": event_id,
        "received_at": received_at,
    }

@router.get("/fundamentals/{symbol}", response_model=FundamentalResponse)
def fundamentals(symbol: str, provider: str = Query("openbb")):
    try:
        return fundamental_metrics(symbol, provider)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(422, str(exc)) from exc

@router.post("/backtest/rsi", response_model=BacktestResponse)
def backtest(req: BacktestRequest):
    try:
        result = rsi_backtest(download_history(req.symbol, req.period), req.initial_cash)
        return {"symbol": req.symbol.upper(), **result}
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(422, str(exc)) from exc

@router.post("/valuation/gordon", response_model=ValuationResponse)
def valuation(req: ValuationRequest):
    try:
        return {"fair_value": gordon_growth_value(req.dividend_per_share, req.growth_rate, req.required_return), "method": "Gordon Growth"}
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

@router.post("/portfolio/optimize", response_model=PortfolioResponse)
def optimize(req: PortfolioRequest):
    try:
        frames = [get_provider("openbb").history(s, req.period)["Close"].rename(s) for s in req.symbols]
        returns = pd.concat(frames, axis=1).dropna().pct_change().dropna()
        w, ret, vol, sharpe = optimize_max_sharpe(returns, req.risk_free_rate)
        frontier = efficient_frontier(returns)
        return {"weights": dict(zip(req.symbols, map(float, w))), "expected_return": float(ret), "volatility": float(vol), "sharpe": float(sharpe), "frontier": frontier}
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(422, str(exc)) from exc

@router.post("/risk/var", response_model=VaRResponse)
def var(req: VaRRequest):
    try:
        symbols = list(req.weights)
        if not symbols:
            raise ValueError("weights cannot be empty")
        frames = [get_provider("openbb").history(s, req.period)["Close"].rename(s) for s in symbols]
        returns = pd.concat(frames, axis=1).dropna().pct_change().dropna()
        value = parametric_var(returns, [req.weights[s] for s in symbols], req.portfolio_value, req.confidence)
        return {"confidence": req.confidence, "daily_var": float(value), "daily_var_pct": float(value / req.portfolio_value)}
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(422, str(exc)) from exc

@router.get("/ai/features/{symbol}", response_model=PredictionResponse)
def ai_features(symbol: str, period: str = "2y"):
    try:
        X, y = build_features(get_provider("openbb").history(symbol, period), horizon=5)
        return {"symbol": symbol.upper(), "horizon_days": 5, "probability_up": None, "model": "xgboost-baseline-not-trained", "status": f"features_ready:{len(X)} labels:{int(y.sum())}"}
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(422, str(exc)) from exc

@router.get("/evaluation/rsi/{symbol}")
def evaluate_rsi(symbol: str, period: str = "5y"):
    try:
        df = download_history(symbol, period)
        result = rsi_backtest(df, 10000)
        equity = pd.Series(result.get("equity_curve", [10000, result["final_equity"]]))
        return {"symbol": symbol.upper(), **trading_metrics(equity)}
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(422, str(exc)) from exc
