from __future__ import annotations

import json

import pandas as pd
import pytest

from app.services.xgboost_oos import XGBoostOOSFold, XGBoostOOSRun
from app.services.xgboost_oos_artifact import (
    artifact_sha256,
    artifact_size,
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
        test_rows=4, folds=2,
        fold_metadata=(
            XGBoostOOSFold(1, index[0], index[0], index[0], index[1]),
            XGBoostOOSFold(2, index[1], index[1], index[2], index[3]),
        ),
    )

def test_configuration_mismatch_is_rejected():
    payload = serialize_xgboost_oos_run(fixture(), symbol="PETR4", configuration=CONFIG)
    expected = dict(CONFIG)
    expected["horizon"] = 10
    with pytest.raises(ValueError, match="configuration mismatch"):
        validate_xgboost_oos_artifact_configuration(payload, expected)

def test_manifest_verifies_digest_and_size(tmp_path):
    artifact = write_xgboost_oos_artifact(tmp_path / "PETR4.json", fixture(), symbol="PETR4", configuration=CONFIG)
    manifest = {
        "schema_version": 1,
        "configuration": {"symbols": ["PETR4"], **CONFIG},
        "symbols": [{
            "symbol": "PETR4", "artifact": "PETR4.json",
            "artifact_size": artifact_size(artifact),
            "artifact_sha256": artifact_sha256(artifact),
            "rows": 4, "quality_valid": True, "oos_folds": 2, "oos_rows": 4,
        }],
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    result = verify_xgboost_oos_shared_manifest(tmp_path, expected_configuration=CONFIG, expected_symbols=("PETR4",))
    assert result["schema_version"] == 1

def test_manifest_rejects_modified_artifact(tmp_path):
    artifact = write_xgboost_oos_artifact(tmp_path / "PETR4.json", fixture(), symbol="PETR4", configuration=CONFIG)
    manifest = {
        "schema_version": 1,
        "configuration": {"symbols": ["PETR4"], **CONFIG},
        "symbols": [{"symbol": "PETR4", "artifact": "PETR4.json",
            "artifact_size": artifact_size(artifact), "artifact_sha256": artifact_sha256(artifact),
            "rows": 4, "quality_valid": True, "oos_folds": 2, "oos_rows": 4}],
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    artifact.write_text(artifact.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        verify_xgboost_oos_shared_manifest(tmp_path, expected_configuration=CONFIG, expected_symbols=("PETR4",))
