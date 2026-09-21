from __future__ import annotations

import json

import pandas as pd
import pytest

from app.services.xgboost_oos import XGBoostOOSFold, XGBoostOOSRun
from app.services.xgboost_oos_artifact import (
    artifact_sha256,
    artifact_size,
    normalized_ohlcv_sha256,
    serialize_xgboost_oos_run,
    validate_xgboost_oos_artifact_configuration,
    verify_xgboost_oos_shared_manifest,
    write_xgboost_oos_artifact,
)

CONFIG = {
    "requested_start": "2021-09-15",
    "requested_end": "2026-09-15",
    "horizon": 5,
    "train_size": 500,
    "test_size": 100,
    "step": 100,
    "threshold": 0.60,
    "initial_cash": 100000.0,
}


def fixture():
    index = pd.date_range("2025-01-01", periods=4, tz="UTC")
    return XGBoostOOSRun(
        predictions=pd.Series([1, 0, 1, 0], index=index, name="prediction"),
        probabilities=pd.Series([0.6, 0.4, 0.7, 0.3], index=index, name="probability"),
        test_rows=4,
        folds=2,
        fold_metadata=(
            XGBoostOOSFold(1, index[0], index[0], index[0], index[1]),
            XGBoostOOSFold(2, index[1], index[1], index[2], index[3]),
        ),
    )


def source_provenance(frame: pd.DataFrame) -> dict:
    return {
        "provider": "openbb/yfinance",
        "symbol": "PETR4",
        "interval": "1d",
        "requested_start": "2021-09-15",
        "requested_end": "2026-09-15",
        "rows": len(frame),
        "data_start": frame.index.min().isoformat(),
        "data_end": frame.index.max().isoformat(),
        "data_sha256": normalized_ohlcv_sha256(frame),
        "quality_valid": True,
        "quality_report": {"valid": True},
    }


def test_configuration_mismatch_is_rejected():
    payload = serialize_xgboost_oos_run(fixture(), symbol="PETR4", configuration=CONFIG)
    expected = dict(CONFIG)
    expected["horizon"] = 10
    with pytest.raises(ValueError, match="configuration mismatch"):
        validate_xgboost_oos_artifact_configuration(payload, expected)


def test_manifest_verifies_digest_and_size(tmp_path):
    history = pd.DataFrame({"Open": [1.0, 2.0], "High": [1.1, 2.1], "Low": [0.9, 1.9], "Close": [1.0, 2.0], "Volume": [10.0, 20.0]}, index=pd.date_range("2025-01-01", periods=2, tz="UTC"))
    provenance = source_provenance(history)
    artifact = write_xgboost_oos_artifact(
        tmp_path / "PETR4.json", fixture(), symbol="PETR4", configuration=CONFIG, source=provenance
    )
    manifest = {
        "schema_version": 1,
        "configuration": {"symbols": ["PETR4"], **CONFIG},
        "symbols": [{
            "symbol": "PETR4",
            "artifact": "PETR4.json",
            "source_provenance": provenance,
            "artifact_size": artifact_size(artifact),
            "artifact_sha256": artifact_sha256(artifact),
            "rows": 4,
            "quality_valid": True,
            "oos_folds": 2,
            "oos_rows": 4,
        }],
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    result = verify_xgboost_oos_shared_manifest(
        tmp_path,
        expected_configuration=CONFIG,
        expected_symbols=("PETR4",),
        expected_source_provider="openbb/yfinance",
        expected_source_interval="1d",
    )
    assert result["schema_version"] == 1


def test_manifest_rejects_modified_artifact(tmp_path):
    history = pd.DataFrame({"Open": [1.0, 2.0], "High": [1.1, 2.1], "Low": [0.9, 1.9], "Close": [1.0, 2.0], "Volume": [10.0, 20.0]}, index=pd.date_range("2025-01-01", periods=2, tz="UTC"))
    provenance = source_provenance(history)
    artifact = write_xgboost_oos_artifact(
        tmp_path / "PETR4.json", fixture(), symbol="PETR4", configuration=CONFIG, source=provenance
    )
    manifest = {
        "schema_version": 1,
        "configuration": {"symbols": ["PETR4"], **CONFIG},
        "symbols": [{
            "symbol": "PETR4",
            "artifact": "PETR4.json",
            "source_provenance": provenance,
            "artifact_size": artifact_size(artifact),
            "artifact_sha256": artifact_sha256(artifact),
            "rows": 4,
            "quality_valid": True,
            "oos_folds": 2,
            "oos_rows": 4,
        }],
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    original = artifact.read_bytes()
    mutated = bytearray(original)
    position = next(index for index, value in enumerate(mutated) if value not in (10, 13, 32))
    mutated[position] = 0x20 if mutated[position] != 0x20 else 0x21
    artifact.write_bytes(mutated)
    assert artifact_size(artifact) == manifest["symbols"][0]["artifact_size"]
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        verify_xgboost_oos_shared_manifest(
            tmp_path,
            expected_configuration=CONFIG,
            expected_symbols=("PETR4",),
            expected_source_provider="openbb/yfinance",
            expected_source_interval="1d",
        )


def test_normalized_ohlcv_digest_is_deterministic() -> None:
    index = pd.date_range("2025-01-01", periods=3, tz="UTC")
    frame = pd.DataFrame(
        {"Open": [1.0, 2.0, 3.0], "High": [1.1, 2.1, 3.1], "Low": [0.9, 1.9, 2.9], "Close": [1.0, 2.0, 3.0], "Volume": [10.0, 20.0, 30.0]},
        index=index,
    )
    assert normalized_ohlcv_sha256(frame) == normalized_ohlcv_sha256(frame.copy())


def test_manifest_rejects_changed_source_provenance(tmp_path):
    artifact = write_xgboost_oos_artifact(
        tmp_path / "PETR4.json", fixture(), symbol="PETR4", configuration=CONFIG,
        source={
            "provider": "openbb/yfinance",
            "symbol": "PETR4",
            "interval": "1d",
            "requested_start": "2021-09-15",
            "requested_end": "2026-09-15",
            "rows": 4,
            "data_start": "2025-01-01T00:00:00+00:00",
            "data_end": "2025-01-04T00:00:00+00:00",
            "data_sha256": "source-digest",
            "quality_valid": True,
            "quality_report": {"valid": True},
        },
    )
    manifest = {
        "schema_version": 1,
        "configuration": {"symbols": ["PETR4"], **CONFIG},
        "symbols": [{
            "symbol": "PETR4",
            "artifact": "PETR4.json",
            "source_provenance": {
                "provider": "openbb/yfinance",
                "symbol": "PETR4",
                "interval": "1d",
                "requested_start": "2021-09-15",
                "requested_end": "2026-09-15",
                "rows": 999,
                "data_start": "2025-01-01T00:00:00+00:00",
                "data_end": "2025-01-04T00:00:00+00:00",
                "data_sha256": "source-digest",
                "quality_valid": True,
                "quality_report": {"valid": True},
            },
            "artifact_size": artifact_size(artifact),
            "artifact_sha256": artifact_sha256(artifact),
            "rows": 4,
            "quality_valid": True,
            "oos_folds": 2,
            "oos_rows": 4,
        }],
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="OOS source provenance mismatch"):
        verify_xgboost_oos_shared_manifest(
            tmp_path,
            expected_configuration=CONFIG,
            expected_symbols=("PETR4",),
            expected_source_provider="openbb/yfinance",
            expected_source_interval="1d",
        )
