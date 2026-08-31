from fastapi import APIRouter, HTTPException
from ..models import HealthResponse, BacktestRequest, BacktestResponse, ValuationRequest, ValuationResponse, PortfolioRequest, PortfolioResponse, VaRRequest, VaRResponse, PredictionResponse
from ..settings import get_settings
from ..services.market_data import download_history
from ..services.technical import indicators
from ..services.backtest import rsi_backtest
from ..services.valuation import gordon_growth_value
from ..services.portfolio import optimize_max_sharpe, parametric_var
from ..services.ml import make_features

router = APIRouter()
settings = get_settings()

@router.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok", "trading_mode": settings.trading_mode.value}

@router.get("/market/{symbol}")
def market(symbol: str, period: str = "1y"):
    try:
        df = indicators(download_history(symbol, period))
        row = df.iloc[-1]
        return {"symbol": symbol.upper(), "close": float(row["Close"]), "ema9": float(row["EMA9"]), "ema21": float(row["EMA21"]), "rsi14": None if row["RSI14"] != row["RSI14"] else float(row["RSI14"])}
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
        frames = [download_history(s, req.period)["Close"].rename(s) for s in req.symbols]
        prices = __import__("pandas").concat(frames, axis=1).dropna()
        returns = prices.pct_change().dropna()
        w, ret, vol, sharpe = optimize_max_sharpe(returns, req.risk_free_rate)
        return {"weights": dict(zip(req.symbols, map(float, w))), "expected_return": float(ret), "volatility": float(vol), "sharpe": float(sharpe)}
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(422, str(exc)) from exc

@router.post("/risk/var", response_model=VaRResponse)
def var(req: VaRRequest):
    try:
        symbols = list(req.weights)
        frames = [download_history(s, req.period)["Close"].rename(s) for s in symbols]
        returns = __import__("pandas").concat(frames, axis=1).dropna().pct_change().dropna()
        weights = [req.weights[s] for s in symbols]
        value = parametric_var(returns, weights, req.portfolio_value, req.confidence)
        return {"confidence": req.confidence, "daily_var": float(value), "daily_var_pct": float(value/req.portfolio_value)}
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(422, str(exc)) from exc

@router.get("/ai/features/{symbol}", response_model=PredictionResponse)
def ai_features(symbol: str, period: str = "2y"):
    try:
        df = make_features(download_history(symbol, period))
        return {"symbol": symbol.upper(), "horizon_days": 5, "probability_up": None, "model": "xgboost-baseline-not-trained", "status": f"features_ready:{len(df)}"}
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(422, str(exc)) from exc
