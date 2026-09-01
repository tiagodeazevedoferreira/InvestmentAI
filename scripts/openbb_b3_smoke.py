from __future__ import annotations

import sys

from backend.app.services.openbb_market_data import OpenBBMarketDataProvider


SYMBOLS = ("PETR4", "VALE3", "ITUB4")


def main() -> int:
    provider = OpenBBMarketDataProvider()
    failures: list[str] = []
    for symbol in SYMBOLS:
        try:
            df, quality = provider.historical_with_quality(symbol, interval="1d")
            print(f"{symbol}: rows={quality.rows} first={df.index.min()} last={df.index.max()}")
        except Exception as exc:  # smoke test should report provider-specific failure clearly
            failures.append(f"{symbol}: {exc}")
    if failures:
        print("OpenBB/B3 smoke validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("OpenBB/B3 smoke validation passed for PETR4, VALE3 and ITUB4")
    return 0


if __name__ == "__main__":
    sys.exit(main())
