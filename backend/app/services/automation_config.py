"""Configuration for the paper automation loop."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PaperAutomationConfig:
    symbols: tuple[str, ...] = ("PETR4", "VALE3", "ITUB4")
    period: str = "6mo"
    target_weight: float = 0.10
    enabled: bool = False

    def __post_init__(self) -> None:
        if not self.symbols:
            raise ValueError("at least one symbol is required")
        if not 0 < self.target_weight <= 1:
            raise ValueError("target_weight must be in (0, 1]")

    @property
    def provider_symbols(self) -> tuple[str, ...]:
        return tuple(s if "." in s else f"{s}.SA" for s in self.symbols)
