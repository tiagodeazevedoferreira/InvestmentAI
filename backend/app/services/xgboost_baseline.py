from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

import pandas as pd

from .features import build_features
from .model_engine import train_xgboost

HistoryProvider = Callable[[str, str], pd.DataFrame]


def train_symbol_baseline(
    symbol: str,
    period: str,
    model_path: str,
    history_provider: HistoryProvider,
    horizon: int = 5,
    params: dict | None = None,
) -> dict:
    """Train an offline XGBoost baseline for one symbol.

    Historical data, feature engineering, training, and model persistence only.
    This function never submits broker orders.
    """
    normalized_symbol = symbol.strip().upper()
    if not normalized_symbol:
        raise ValueError("symbol cannot be empty")
    if not period.strip():
        raise ValueError("period cannot be empty")
    if not callable(history_provider):
        raise ValueError("history_provider must be callable")

    history = history_provider(normalized_symbol, period)
    if not isinstance(history, pd.DataFrame):
        raise ValueError("history_provider must return a pandas DataFrame")

    X, y = build_features(history, horizon=horizon)
    metadata = train_xgboost(X, y, model_path, params=params)
    metadata.update(
        {
            "symbol": normalized_symbol,
            "period": period,
            "horizon": horizon,
            "training_samples": int(len(X)),
            "positive_labels": int(y.sum()),
        }
    )

    metadata_path = Path(model_path).with_suffix(".meta.json")
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata
