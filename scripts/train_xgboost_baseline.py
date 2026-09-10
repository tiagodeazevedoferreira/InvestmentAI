from __future__ import annotations

import argparse
from pathlib import Path

from app.services.providers import get_provider
from app.services.xgboost_baseline import train_symbol_baseline


def main() -> int:
    parser = argparse.ArgumentParser(description="Train an offline XGBoost baseline")
    parser.add_argument("symbol")
    parser.add_argument("--period", default="5y")
    parser.add_argument("--horizon", type=int, default=5)
    parser.add_argument("--provider", default="openbb")
    parser.add_argument("--model", default=None)
    args = parser.parse_args()

    model_path = args.model or str(Path("models") / "xgboost" / f"{args.symbol.upper()}.json")
    provider = get_provider(args.provider)
    metadata = train_symbol_baseline(
        args.symbol,
        args.period,
        model_path,
        provider.history,
        horizon=args.horizon,
    )

    print(f"symbol={metadata['symbol']}")
    print(f"period={metadata['period']}")
    print(f"samples={metadata['training_samples']}")
    print(f"positive_labels={metadata['positive_labels']}")
    print(f"model={metadata['model_path']}")
    print(f"metadata={metadata['metadata_path']}")
    print(f"metrics={metadata['metrics']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
