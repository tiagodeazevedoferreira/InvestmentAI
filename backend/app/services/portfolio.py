from __future__ import annotations
import numpy as np
from scipy.optimize import minimize
from scipy.stats import norm


def optimize_max_sharpe(returns, risk_free_rate=0.0):
    mu = np.asarray(returns.mean() * 252, dtype=float)
    cov = np.asarray(returns.cov() * 252, dtype=float)
    n = len(mu)
    if n < 2 or n > 5:
        raise ValueError("Portfolio optimizer supports 2 to 5 assets")
    if not np.isfinite(mu).all() or not np.isfinite(cov).all():
        raise ValueError("returns contain insufficient or invalid data")
    def neg_sharpe(w):
        vol = np.sqrt(max(w @ cov @ w, 0))
        return 1e6 if vol <= 0 else -(w @ mu - risk_free_rate) / vol
    result = minimize(neg_sharpe, np.ones(n) / n, method="SLSQP", bounds=[(0, 1)] * n,
                      constraints={"type": "eq", "fun": lambda w: w.sum() - 1},
                      options={"maxiter": 1000, "ftol": 1e-12})
    if not result.success:
        raise RuntimeError(f"Portfolio optimization failed: {result.message}")
    w = result.x
    vol = np.sqrt(max(w @ cov @ w, 0))
    ret = w @ mu
    return w, ret, vol, (ret - risk_free_rate) / vol if vol else 0.0


def efficient_frontier(returns, points=25):
    if points < 2:
        raise ValueError("points must be >= 2")
    mu = np.asarray(returns.mean() * 252, dtype=float)
    cov = np.asarray(returns.cov() * 252, dtype=float)
    n = len(mu)
    if n < 2 or n > 5:
        raise ValueError("Portfolio optimizer supports 2 to 5 assets")
    out = []
    for target in np.linspace(mu.min(), mu.max(), points):
        fun = lambda w: float(w @ cov @ w)
        constraints = [{"type": "eq", "fun": lambda w: w.sum() - 1}, {"type": "eq", "fun": lambda w, t=target: w @ mu - t}]
        res = minimize(fun, np.ones(n) / n, method="SLSQP", bounds=[(0, 1)] * n, constraints=constraints)
        if res.success:
            vol = float(np.sqrt(max(res.fun, 0)))
            out.append({"target_return": float(target), "volatility": vol, "weights": res.x.tolist()})
    return out


def parametric_var(returns, weights, portfolio_value, confidence=0.95):
    if portfolio_value <= 0:
        raise ValueError("portfolio_value must be positive")
    if not 0.5 < confidence < 1:
        raise ValueError("confidence must be between 0.5 and 1")
    w = np.asarray(weights, dtype=float)
    if len(w) != len(returns.columns) or not np.isfinite(w).all():
        raise ValueError("weights do not match return columns")
    if not np.isclose(w.sum(), 1.0, atol=1e-6):
        raise ValueError("weights must sum to 1")
    cov = np.asarray(returns.cov(), dtype=float)
    sigma = float(np.sqrt(max(w @ cov @ w, 0)))
    return float(norm.ppf(confidence) * sigma * portfolio_value)
