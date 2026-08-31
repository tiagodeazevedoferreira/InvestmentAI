from __future__ import annotations
from datetime import datetime, timezone
from ..firebase import get_db

MAX_HISTORY_ROWS = 500


def write_feature_snapshot(symbol: str, features: dict):
    db = get_db()
    if db is None:
        raise RuntimeError("Firebase is not configured")
    now = datetime.now(timezone.utc).isoformat()
    ref = db.reference(f"feature_snapshots/{symbol.upper()}")
    ref.push({"timestamp": now, "features": features})


def write_operational_state(path: str, payload: dict):
    db = get_db()
    if db is None:
        raise RuntimeError("Firebase is not configured")
    db.reference(path.strip("/")).set(payload)
