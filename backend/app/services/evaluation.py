from __future__ import annotations
import numpy as np
import pandas as pd


def classification_metrics(y_true, probability, threshold=.5) -> dict:
    y = np.asarray(y_true, dtype=int)
    p = np.asarray(probability, dtype=float)
    pred = (p >= threshold).astype(int)
    return {
        "accuracy": float((pred == y).mean()) if len(y) else 0.0,
        "directional_accuracy": float((pred == y).mean()) if len(y) else 0.0,
        "samples": int(len(y)),
    }


def trading_metrics(equity: pd.Series, periods_per_year=252) -> dict:
    if equity is None or len(equity) < 2:
        raise ValueError("At least two equity observations are required")
    e = equity.astype(float).replace([np.inf, -np.inf], np.nan).dropna()
    r = e.pct_change().dropna()
    total = float(e.iloc[-1] / e.iloc[0] - 1)
    ann = float((1 + total) ** (periods_per_year / max(len(r), 1)) - 1) if total > -1 else -1.0
    vol = float(r.std(ddof=1) * np.sqrt(periods_per_year)) if len(r) > 1 else 0.0
    sharpe = float((r.mean() / r.std(ddof=1)) * np.sqrt(periods_per_year)) if r.std(ddof=1) > 0 else 0.0
    downside = r[r < 0].std(ddof=1)
    sortino = float((r.mean() / downside) * np.sqrt(periods_per_year)) if pd.notna(downside) and downside > 0 else 0.0
    peak = e.cummax()
    drawdown = e / peak - 1
    mdd = float(drawdown.min())
    calmar = float(ann / abs(mdd)) if mdd < 0 else 0.0
    return {"total_return": total, "annualized_return": ann, "volatility": vol, "sharpe": sharpe, "sortino": sortino, "max_drawdown": mdd, "calmar": calmar}
