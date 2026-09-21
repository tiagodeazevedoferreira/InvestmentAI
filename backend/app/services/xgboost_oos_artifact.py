from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .xgboost_oos import XGBoostOOSFold, XGBoostOOSRun

SCHEMA_VERSION = 1
MANIFEST_SCHEMA_VERSION = 1
OOS_CONFIGURATION_KEYS = (
    "requested_start",
    "requested_end",
    "horizon",
    "train_size",
    "test_size",
    "step",
    "threshold",
    "initial_cash",
)


def _timestamp(value: pd.Timestamp) -> str:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")
    return timestamp.isoformat()


def _parse_timestamp(value: str) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")
    return timestamp


def serialize_xgboost_oos_run(
    oos: XGBoostOOSRun, *, symbol: str, configuration: dict, source: dict | None = None,
) -> dict:
    if not isinstance(oos, XGBoostOOSRun):
        raise ValueError("oos must be an XGBoostOOSRun")
    normalized_symbol = symbol.strip().upper()
    if not normalized_symbol:
        raise ValueError("symbol cannot be empty")
    if not isinstance(configuration, dict):
        raise ValueError("configuration must be a dictionary")
    if not oos.probabilities.index.equals(oos.predictions.index):
        raise ValueError("OOS predictions and probabilities must have identical indexes")
    if not oos.probabilities.index.is_unique or not oos.probabilities.index.is_monotonic_increasing:
        raise ValueError("OOS prediction index must be unique and chronological")
    probabilities = oos.probabilities.astype(float)
    predictions = oos.predictions.astype(int)
    values = probabilities.to_numpy(dtype=float)
    if not np.isfinite(values).all() or not ((values >= 0.0) & (values <= 1.0)).all():
        raise ValueError("OOS probabilities must be finite and within [0, 1]")
    if not predictions.isin([0, 1]).all():
        raise ValueError("OOS predictions must be binary")
    if len(probabilities) != oos.test_rows or len(oos.fold_metadata) != oos.folds:
        raise ValueError("OOS size metadata is inconsistent")
    rows = [
        {
            "timestamp": _timestamp(index),
            "prediction": int(predictions.loc[index]),
            "probability": float(probabilities.loc[index]),
        }
        for index in probabilities.index
    ]
    folds = [
        {
            "fold": int(fold.fold),
            "train_start": _timestamp(fold.train_start),
            "train_end": _timestamp(fold.train_end),
            "test_start": _timestamp(fold.test_start),
            "test_end": _timestamp(fold.test_end),
        }
        for fold in oos.fold_metadata
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "symbol": normalized_symbol,
        "configuration": configuration,
        "source": source or {},
        "test_rows": int(oos.test_rows),
        "folds": int(oos.folds),
        "predictions": rows,
        "fold_metadata": folds,
    }


def validate_xgboost_oos_artifact_configuration(
    payload: dict,
    expected_configuration: dict,
) -> None:
    if not isinstance(payload, dict):
        raise ValueError("OOS artifact payload must be a dictionary")
    configuration = payload.get("configuration")
    if not isinstance(configuration, dict):
        raise ValueError("OOS artifact configuration must be a dictionary")
    if not isinstance(expected_configuration, dict):
        raise ValueError("expected configuration must be a dictionary")
    missing = [key for key in OOS_CONFIGURATION_KEYS if key not in configuration]
    if missing:
        raise ValueError(f"OOS artifact configuration is missing keys: {missing}")
    mismatches = []
    for key in OOS_CONFIGURATION_KEYS:
        if key in expected_configuration and configuration.get(key) != expected_configuration[key]:
            mismatches.append(
                f"{key}: artifact={configuration.get(key)!r}, expected={expected_configuration[key]!r}"
            )
    if mismatches:
        raise ValueError("OOS artifact configuration mismatch: " + "; ".join(mismatches))


def artifact_sha256(path: str | Path) -> str:
    artifact_path = Path(path)
    try:
        return hashlib.sha256(artifact_path.read_bytes()).hexdigest()
    except OSError as exc:
        raise ValueError(f"unable to hash OOS artifact: {artifact_path}") from exc


def artifact_size(path: str | Path) -> int:
    artifact_path = Path(path)
    try:
        return artifact_path.stat().st_size
    except OSError as exc:
        raise ValueError(f"unable to stat OOS artifact: {artifact_path}") from exc


def normalized_ohlcv_sha256(frame: pd.DataFrame) -> str:
    """Return a deterministic digest for the normalized OHLCV input frame."""
    if not isinstance(frame, pd.DataFrame):
        raise ValueError("source market data must be a DataFrame")
    if frame.index.empty:
        raise ValueError("source market data cannot be empty")
    normalized = frame.copy()
    if not isinstance(normalized.index, pd.DatetimeIndex):
        raise ValueError("source market data index must be DatetimeIndex")
    index = normalized.index
    if index.tz is None:
        index = index.tz_localize("UTC")
    else:
        index = index.tz_convert("UTC")
    normalized.index = index
    normalized = normalized.sort_index()
    hasher = hashlib.sha256()
    hasher.update(json.dumps(list(map(str, normalized.columns)), separators=(",", ":")).encode("utf-8"))
    hasher.update(json.dumps([str(dtype) for dtype in normalized.dtypes], separators=(",", ":")).encode("utf-8"))
    hasher.update(pd.util.hash_pandas_object(normalized, index=True).to_numpy(dtype="uint64").tobytes())
    return hasher.hexdigest()


def validate_xgboost_oos_artifact_source(
    payload: dict,
    *,
    expected_provider: str,
    expected_symbol: str,
    expected_requested_start: str,
    expected_requested_end: str,
    expected_rows: int,
    expected_data_start: str,
    expected_data_end: str,
    expected_data_sha256: str,
    expected_quality_report: dict,
) -> None:
    if not isinstance(payload, dict):
        raise ValueError("OOS artifact payload must be a dictionary")
    source = payload.get("source")
    if not isinstance(source, dict):
        raise ValueError("OOS artifact source provenance must be a dictionary")
    expected = {
        "provider": expected_provider,
        "symbol": expected_symbol.strip().upper(),
        "requested_start": expected_requested_start,
        "requested_end": expected_requested_end,
        "rows": int(expected_rows),
        "data_start": expected_data_start,
        "data_end": expected_data_end,
        "data_sha256": expected_data_sha256,
        "quality_report": expected_quality_report,
    }
    for key, value in expected.items():
        if source.get(key) != value:
            raise ValueError(
                f"OOS artifact source provenance mismatch for {key}: "
                f"artifact={source.get(key)!r}, expected={value!r}"
            )


def deserialize_xgboost_oos_run(payload: dict) -> XGBoostOOSRun:
    if not isinstance(payload, dict) or payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported OOS artifact schema_version")
    if not isinstance(payload.get("symbol"), str) or not payload["symbol"].strip():
        raise ValueError("OOS artifact symbol must be non-empty")
    if not isinstance(payload.get("configuration"), dict):
        raise ValueError("OOS artifact configuration must be a dictionary")
    rows = payload.get("predictions")
    fold_rows = payload.get("fold_metadata")
    if not isinstance(rows, list) or not rows:
        raise ValueError("OOS artifact predictions must be a non-empty list")
    if not isinstance(fold_rows, list) or not fold_rows:
        raise ValueError("OOS artifact fold_metadata must be a non-empty list")
    index = pd.DatetimeIndex([_parse_timestamp(row["timestamp"]) for row in rows])
    if not index.is_unique or not index.is_monotonic_increasing:
        raise ValueError("OOS artifact prediction timestamps must be unique and chronological")
    predictions = pd.Series(
        [int(row["prediction"]) for row in rows],
        index=index,
        name="prediction",
        dtype=int,
    )
    probabilities = pd.Series(
        [float(row["probability"]) for row in rows],
        index=index,
        name="probability",
        dtype=float,
    )
    if not predictions.isin([0, 1]).all():
        raise ValueError("OOS artifact predictions must be binary")
    values = probabilities.to_numpy(dtype=float)
    if not np.isfinite(values).all() or not ((values >= 0.0) & (values <= 1.0)).all():
        raise ValueError("OOS artifact probabilities must be finite and within [0, 1]")
    folds = []
    for row in fold_rows:
        fold = XGBoostOOSFold(
            fold=int(row["fold"]),
            train_start=_parse_timestamp(row["train_start"]),
            train_end=_parse_timestamp(row["train_end"]),
            test_start=_parse_timestamp(row["test_start"]),
            test_end=_parse_timestamp(row["test_end"]),
        )
        if fold.test_start > fold.test_end or fold.train_start > fold.train_end:
            raise ValueError("OOS artifact fold ranges are invalid")
        folds.append(fold)
    if [fold.fold for fold in folds] != list(range(1, len(folds) + 1)):
        raise ValueError("OOS artifact fold numbering must be contiguous from 1")
    for fold in folds:
        if fold.test_start not in index or fold.test_end not in index:
            raise ValueError("OOS artifact fold test range is outside prediction timestamps")
    for previous, current in zip(folds, folds[1:]):
        if previous.test_end >= current.test_start:
            raise ValueError("OOS artifact fold test windows overlap")
    if len(predictions) != int(payload.get("test_rows", -1)) or len(folds) != int(payload.get("folds", -1)):
        raise ValueError("OOS artifact size metadata is inconsistent")
    return XGBoostOOSRun(
        predictions=predictions,
        probabilities=probabilities,
        test_rows=len(predictions),
        folds=len(folds),
        fold_metadata=tuple(folds),
    )


def write_xgboost_oos_artifact(
    path: str | Path,
    oos: XGBoostOOSRun,
    *,
    symbol: str,
    configuration: dict,
    source: dict | None = None,
) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = serialize_xgboost_oos_run(
        oos,
        symbol=symbol,
        configuration=configuration,
        source=source,
    )
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output


def load_xgboost_oos_artifact(path: str | Path) -> tuple[XGBoostOOSRun, dict]:
    artifact_path = Path(path)
    try:
        payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"unable to read OOS artifact: {artifact_path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid OOS artifact JSON: {artifact_path}") from exc
    return deserialize_xgboost_oos_run(payload), payload


def verify_xgboost_oos_shared_manifest(
    directory: str | Path,
    *,
    expected_configuration: dict,
    expected_symbols: tuple[str, ...] | list[str],
    expected_source_provider: str | None = None,
    expected_source_interval: str | None = None,
) -> dict:
    root = Path(directory)
    manifest_path = root / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"unable to read OOS manifest: {manifest_path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid OOS manifest JSON: {manifest_path}") from exc

    if manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        raise ValueError("unsupported OOS manifest schema_version")
    symbols = tuple(str(symbol).upper() for symbol in manifest.get("configuration", {}).get("symbols", []))
    expected = tuple(str(symbol).upper() for symbol in expected_symbols)
    if symbols != expected:
        raise ValueError(f"OOS manifest symbols mismatch: manifest={symbols}, expected={expected}")
    manifest_configuration = manifest.get("configuration")
    if not isinstance(manifest_configuration, dict):
        raise ValueError("OOS manifest configuration must be a dictionary")
    for key, value in expected_configuration.items():
        if manifest_configuration.get(key) != value:
            raise ValueError(
                f"OOS manifest configuration mismatch for {key}: "
                f"manifest={manifest_configuration.get(key)!r}, expected={value!r}"
            )

    entries = manifest.get("symbols")
    if not isinstance(entries, list) or len(entries) != len(expected):
        raise ValueError("OOS manifest symbols entries are inconsistent")
    verified = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("OOS manifest symbol entry must be a dictionary")
        symbol = str(entry.get("symbol", "")).upper()
        if symbol not in expected:
            raise ValueError(f"unexpected OOS manifest symbol: {symbol}")
        artifact_name = entry.get("artifact")
        if not isinstance(artifact_name, str) or Path(artifact_name).name != artifact_name:
            raise ValueError(f"invalid OOS artifact filename for {symbol}")
        artifact_path = root / artifact_name
        if not artifact_path.is_file():
            raise ValueError(f"missing OOS artifact for {symbol}: {artifact_path}")
        recorded_size = entry.get("artifact_size")
        recorded_sha = entry.get("artifact_sha256")
        if int(recorded_size) != artifact_size(artifact_path):
            raise ValueError(f"OOS artifact size mismatch for {symbol}")
        if str(recorded_sha) != artifact_sha256(artifact_path):
            raise ValueError(f"OOS artifact SHA-256 mismatch for {symbol}")
        oos, payload = load_xgboost_oos_artifact(artifact_path)
        if str(payload.get("symbol", "")).upper() != symbol:
            raise ValueError(f"OOS artifact symbol mismatch for {symbol}")
        validate_xgboost_oos_artifact_configuration(payload, expected_configuration)
        source = payload.get("source")
        entry_source = entry.get("source_provenance")
        if not isinstance(entry_source, dict):
            raise ValueError(f"OOS manifest source provenance is missing for {symbol}")
        if not isinstance(source, dict):
            raise ValueError(f"OOS artifact source provenance is missing for {symbol}")
        for key, value in entry_source.items():
            if source.get(key) != value:
                raise ValueError(f"OOS source provenance mismatch for {symbol}: {key}")
        if expected_source_provider is not None and source.get("provider") != expected_source_provider:
            raise ValueError(f"OOS source provider mismatch for {symbol}")
        if expected_source_interval is not None and source.get("interval") != expected_source_interval:
            raise ValueError(f"OOS source interval mismatch for {symbol}")
        if source.get("symbol") != symbol:
            raise ValueError(f"OOS source symbol mismatch for {symbol}")
        required_source_keys = {
            "provider", "symbol", "interval", "requested_start", "requested_end",
            "rows", "data_start", "data_end", "data_sha256", "quality_valid", "quality_report",
        }
        if not required_source_keys.issubset(source):
            raise ValueError(f"OOS source provenance is incomplete for {symbol}")
        if int(source.get("rows", -1)) != int(entry.get("source_provenance", {}).get("rows", -2)):
            raise ValueError(f"OOS source row metadata mismatch for {symbol}")
        if int(entry.get("oos_folds", -1)) != oos.folds or int(entry.get("oos_rows", -1)) != oos.test_rows:
            raise ValueError(f"OOS manifest size metadata mismatch for {symbol}")
        verified.append({"symbol": symbol, "artifact": artifact_name, "sha256": artifact_sha256(artifact_path)})
    if {entry["symbol"] for entry in verified} != set(expected):
        raise ValueError("OOS manifest does not contain exactly the expected symbols")
    return manifest
