from enum import Enum
from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TradingMode(str, Enum):
    SIMULATION = "simulation"
    PAPER = "paper"
    DEMO = "demo"
    LIVE = "live"


class Settings(BaseSettings):
    app_name: str = "InvestmentAI"
    environment: str = "development"
    trading_mode: TradingMode = TradingMode.SIMULATION
    firebase_database_url: str | None = None
    firebase_service_account: str | None = None
    market_data_timeout_seconds: int = 20
    max_firebase_write_bytes: int = 900_000
    model_min_probability: float = 0.65
    live_trading_enabled: bool = False
    model_approved: bool = False
    risk_gate_enabled: bool = True
    tradingview_webhook_secret: str | None = None
    paper_initial_cash: float = 100_000.0
    paper_fee_bps: float = 5.0
    paper_slippage_bps: float = 5.0
    paper_account_path: str = "paper/account"
    paper_max_order_notional: float = 10_000.0
    xgboost_model_dir: str = "models/xgboost"

    # MT5/Doto connection settings. No password is stored here: the desktop
    # Doto Global MT5 terminal must already be authenticated.
    # DOTO_MT5_TERMINAL_PATH is the canonical runtime variable used by the
    # Doto/MT5 validation tooling; MT5_TERMINAL_PATH remains accepted for
    # backwards compatibility.
    mt5_terminal_path: str | None = Field(
        default=None,
        validation_alias=AliasChoices("DOTO_MT5_TERMINAL_PATH", "MT5_TERMINAL_PATH"),
    )
    mt5_expected_login: int | None = None
    mt5_expected_server: str = "DOTOGlobal-Real"

    # DEMO execution is fail-closed. Both account identity and explicit enablement
    # are required before the MT5 demo adapter can submit an order.
    mt5_demo_execution_enabled: bool = False
    mt5_demo_expected_login: int | None = None
    mt5_demo_expected_server: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
