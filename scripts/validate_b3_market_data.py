from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(BACKEND))

from backend.app.services.data_quality import validate_market_data
from backend.app.services.openbb_market_data import OpenBBMarketDataProvider

SYMBOLS = ("PETR4", "VALE3", "ITUB4")
START = "2021-01-01"
END = "2026-09-01"


def main() -> int:
    provider = OpenBBMarketDataProvider()
    reports = []
    for symbol in SYMBOLS:
        try:
            df = provider.historical(symbol, start=START, end=END, interval="1d")
            report = validate_market_data(symbol, df, interval="1d")
            reports.append(report.__dict__)
            print(json.dumps(report.__dict__, ensure_ascii=False, sort_keys=True))
        except Exception as exc:
            reports.append({"symbol": symbol, "error": str(exc), "valid": False})
            print(json.dumps(reports[-1], ensure_ascii=False, sort_keys=True))

    output = ROOT / "artifacts"
    output.mkdir(exist_ok=True)
    (output / "b3_market_data_quality.json").write_text(
        json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return 0 if all(r.get("valid", False) for r in reports) else 1


if __name__ == "__main__":
    raise SystemExit(main())
