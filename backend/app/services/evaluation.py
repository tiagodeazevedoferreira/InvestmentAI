from __future__ import annotations

import numpy as np
import pandas as pd


def classification_metrics(y_true, probability, threshold=0.5) -> dict:
    y = np.asarray(y_true, dtype=int)
    p = np.asarray(probability, dtype=float)

    if len(y) != len(p):
        raise ValueError("y_true and probability must have the same length")

    if len(y) == 0:
        return {
            "accuracy": 0.0,
            "directional_accuracy": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "roc_auc": None,
            "samples": 0,
        }

    pred = (p >= threshold).astype(int)

    tp = int(((pred == 1) & (y == 1)).sum())
    fp = int(((pred == 1) & (y == 0)).sum())
    fn = int(((pred == 0) & (y == 1)).sum())

    accuracy = float((pred == y).mean())
    precision = float(tp / (tp + fp)) if (tp + fp) else 0.0
    recall = float(tp / (tp + fn)) if (tp + fn) else 0.0

    unique_classes = np.unique(y)
    if len(unique_classes) == 2:
        order = np.argsort(p)
        sorted_y = y[order]
        ranks = np.arange(1, len(y) + 1, dtype=float)
        positive_ranks = ranks[sorted_y == 1]
        n_positive = int((y == 1).sum())
        n_negative = int((y == 0).sum())
        roc_auc = float(
            (positive_ranks.sum() - n_positive * (n_positive + 1) / 2)
            / (n_positive * n_negative)
        )
    else:
        roc_auc = None

    return {
        "accuracy": accuracy,
        "directional_accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "roc_auc": roc_auc,
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
