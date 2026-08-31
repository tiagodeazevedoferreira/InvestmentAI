import numpy as np
from scipy.optimize import minimize

def optimize_max_sharpe(returns, risk_free_rate=0.0):
    mu = np.asarray(returns.mean() * 252, dtype=float)
    cov = np.asarray(returns.cov() * 252, dtype=float)
    n = len(mu)
    if n < 2 or n > 5:
        raise ValueError("Portfolio optimizer supports 2 to 5 assets")
    def neg_sharpe(w):
        vol = np.sqrt(max(w @ cov @ w, 0))
        return 1e6 if vol == 0 else -(w @ mu - risk_free_rate) / vol
    result = minimize(neg_sharpe, np.ones(n) / n, method="SLSQP", bounds=[(0,1)]*n,
                      constraints={"type":"eq", "fun":lambda w: w.sum()-1},
                      options={"maxiter":1000, "ftol":1e-12})
    if not result.success:
        raise RuntimeError(f"Portfolio optimization failed: {result.message}")
    w = result.x
    vol = np.sqrt(w @ cov @ w)
    ret = w @ mu
    return w, ret, vol, (ret-risk_free_rate)/vol if vol else 0.0

def parametric_var(returns, weights, portfolio_value, confidence=0.95):
    if portfolio_value <= 0:
        raise ValueError("portfolio_value must be positive")
    if not 0.5 < confidence < 1:
        raise ValueError("confidence must be between 0.5 and 1")
    w = np.asarray(weights, dtype=float)
    cov = np.asarray(returns.cov(), dtype=float)
    sigma = float(np.sqrt(max(w @ cov @ w, 0)))
    from scipy.stats import norm
    z = norm.ppf(confidence)
    return z * sigma * portfolio_value
