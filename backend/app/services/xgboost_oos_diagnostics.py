from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .xgboost_oos import XGBoostOOSRun


PROBABILITY_BINS = (0.0, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.90, 1.0)
RETURN_HORIZONS = (1, 3, 5, 10)


@dataclass(frozen=True)
class XGBoostSignalDiagnostics:
    symbol: str
    rows: int
    oos_rows: int
    threshold: float
    active_ratio: float
    signal_entries: int
    signal_exits: int
    signal_transitions: int
    holding_periods_bars: tuple[int, ...]
    probability_distribution: dict[str, float]
    probability_bins: tuple[dict, ...]
    conditional_returns: dict[str, dict[str, float | int | None]]
    entry_holding_analysis: tuple[dict, ...]
    conditional_return_observations_5d: tuple[dict, ...]


def _probability_distribution(probabilities: pd.Series) -> dict[str, float]:
    values = probabilities.astype(float)
    return {
        "mean": float(values.mean()),
        "std": float(values.std(ddof=0)),
        "min": float(values.min()),
        "p05": float(values.quantile(0.05)),
        "p25": float(values.quantile(0.25)),
        "p50": float(values.quantile(0.50)),
        "p75": float(values.quantile(0.75)),
        "p95": float(values.quantile(0.95)),
        "max": float(values.max()),
    }


def _future_returns(close: pd.Series, horizon: int) -> pd.Series:
    return close.shift(-horizon) / close - 1.0


def _probability_bins(probabilities: pd.Series, close: pd.Series) -> tuple[dict, ...]:
    rows: list[dict] = []
    buckets = pd.cut(
        probabilities.astype(float),
        bins=list(PROBABILITY_BINS),
        include_lowest=True,
        right=True,
    )
    for bucket, indexes in probabilities.groupby(buckets, observed=True).groups.items():
        p = probabilities.loc[indexes].astype(float)
        row: dict = {
            "bucket": str(bucket),
            "rows": int(len(p)),
            "mean_probability": float(p.mean()),
        }
        for horizon in RETURN_HORIZONS:
            returns = _future_returns(close, horizon).reindex(indexes).dropna()
            row[f"future_return_{horizon}d_rows"] = int(len(returns))
            row[f"future_return_{horizon}d_mean"] = float(returns.mean()) if len(returns) else None
            row[f"future_return_{horizon}d_median"] = float(returns.median()) if len(returns) else None
            row[f"future_return_{horizon}d_positive_rate"] = float((returns > 0).mean()) if len(returns) else None
        rows.append(row)
    return tuple(rows)


def _holding_periods(signals: pd.Series) -> tuple[int, ...]:
    values = signals.astype(int).to_numpy()
    periods: list[int] = []
    current = 0
    for value in values:
        if value > 0:
            current += 1
        elif current:
            periods.append(current)
            current = 0
    if current:
        periods.append(current)
    return tuple(periods)


def _entry_holding_analysis(
    probabilities: pd.Series,
    close: pd.Series,
    threshold: float,
) -> tuple[dict, ...]:
    """Measure what happened after each entry, including counterfactual holds."""
    signals = probabilities.ge(threshold)
    changes = signals.astype(int).diff().fillna(signals.astype(int))
    entry_indexes = probabilities.index[changes == 1]
    signal_values = signals.to_numpy(dtype=int)
    index_positions = {timestamp: position for position, timestamp in enumerate(probabilities.index)}

    rows: list[dict] = []
    for entry_timestamp in entry_indexes:
        entry_position = index_positions[entry_timestamp]
        exit_position = entry_position
        while exit_position + 1 < len(signal_values) and signal_values[exit_position + 1] == 1:
            exit_position += 1

        entry_close = float(close.loc[entry_timestamp])
        exit_timestamp = probabilities.index[exit_position]
        row: dict = {
            "entry_timestamp": pd.Timestamp(entry_timestamp).isoformat(),
            "entry_probability": float(probabilities.loc[entry_timestamp]),
            "actual_holding_bars": int(exit_position - entry_position + 1),
            "exit_timestamp": pd.Timestamp(exit_timestamp).isoformat(),
            "actual_exit_return": float(close.loc[exit_timestamp] / entry_close - 1.0),
        }
        for horizon in RETURN_HORIZONS:
            future_position = entry_position + horizon
            row[f"future_return_{horizon}d"] = (
                float(close.iloc[future_position] / entry_close - 1.0)
                if future_position < len(close.index)
                else None
            )
        rows.append(row)
    return tuple(rows)


def _conditional_return_observations_5d(
    probabilities: pd.Series,
    close: pd.Series,
    threshold: float,
) -> tuple[dict, ...]:
    returns = _future_returns(close, 5).reindex(probabilities.index)
    signals = probabilities.ge(threshold)
    rows: list[dict] = []
    for timestamp, value in returns.items():
        if pd.isna(value):
            continue
        rows.append({
            "timestamp": pd.Timestamp(timestamp).isoformat(),
            "regime": "long" if bool(signals.loc[timestamp]) else "cash",
            "future_return_5d": float(value),
        })
    return tuple(rows)


def _conditional_returns(
    probabilities: pd.Series,
    close: pd.Series,
    threshold: float,
) -> dict[str, dict[str, float | int | None]]:
    signals = probabilities.ge(threshold)
    output: dict[str, dict[str, float | int | None]] = {}
    for name, mask in (("long", signals), ("cash", ~signals)):
        row: dict[str, float | int | None] = {"rows": int(mask.sum())}
        for horizon in RETURN_HORIZONS:
            returns = _future_returns(close, horizon).reindex(probabilities.index)
            returns = returns[mask].dropna()
            row[f"future_return_{horizon}d_rows"] = int(len(returns))
            row[f"future_return_{horizon}d_mean"] = float(returns.mean()) if len(returns) else None
            row[f"future_return_{horizon}d_median"] = float(returns.median()) if len(returns) else None
            row[f"future_return_{horizon}d_positive_rate"] = float((returns > 0).mean()) if len(returns) else None
        output[name] = row
    return output


def diagnose_xgboost_oos_signals(
    history: pd.DataFrame,
    *,
    symbol: str,
    oos: XGBoostOOSRun,
    threshold: float = 0.60,
) -> XGBoostSignalDiagnostics:
    if not isinstance(history, pd.DataFrame):
        raise ValueError("history must be a pandas DataFrame")
    if not isinstance(oos, XGBoostOOSRun):
        raise ValueError("oos must be an XGBoostOOSRun")
    if not np.isfinite(threshold) or not 0.0 < threshold < 1.0:
        raise ValueError("threshold must be finite and strictly between 0 and 1")

    column_map = {str(column).lower(): column for column in history.columns}
    if "close" not in column_map:
        raise ValueError("history is missing required close column")

    close = history[column_map["close"]].astype(float)
    probabilities = oos.probabilities.astype(float)
    if probabilities.empty:
        raise ValueError("OOS probabilities cannot be empty")
    if not probabilities.index.is_unique:
        raise ValueError("OOS probability index must be unique")
    if not probabilities.index.is_monotonic_increasing:
        raise ValueError("OOS probability index must be chronological")
    if not probabilities.index.isin(close.index).all():
        raise ValueError("OOS prediction timestamps must be present in history")
    if not np.isfinite(probabilities.to_numpy()).all():
        raise ValueError("OOS probabilities must be finite")

    signals = probabilities.ge(threshold).astype(int)
    changes = signals.diff().fillna(signals)
    entries = int((changes == 1).sum())
    exits = int((changes == -1).sum())
    periods = _holding_periods(signals)

    return XGBoostSignalDiagnostics(
        symbol=symbol.strip().upper(),
        rows=int(len(history)),
        oos_rows=int(len(probabilities)),
        threshold=float(threshold),
        active_ratio=float(signals.mean()),
        signal_entries=entries,
        signal_exits=exits,
        signal_transitions=entries + exits,
        holding_periods_bars=periods,
        probability_distribution=_probability_distribution(probabilities),
        probability_bins=_probability_bins(probabilities, close),
        conditional_returns=_conditional_returns(probabilities, close, threshold),
        entry_holding_analysis=_entry_holding_analysis(probabilities, close, threshold),
        conditional_return_observations_5d=_conditional_return_observations_5d(probabilities, close, threshold),
    )
