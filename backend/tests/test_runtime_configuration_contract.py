from pathlib import Path

from app.settings import Settings


def test_production_runtime_template_covers_all_settings_fields():
    template = (
        Path(__file__).resolve().parents[2] / "deploy" / "production.env.example"
    ).read_text(encoding="utf-8")
    declared = {
        line.split("=", 1)[0]
        for line in template.splitlines()
        if line and not line.startswith("#") and "=" in line
    }

    expected = {
        "APP_NAME",
        "ENVIRONMENT",
        "TRADING_MODE",
        "FIREBASE_DATABASE_URL",
        "FIREBASE_SERVICE_ACCOUNT",
        "MARKET_DATA_TIMEOUT_SECONDS",
        "MAX_FIREBASE_WRITE_BYTES",
        "MODEL_MIN_PROBABILITY",
        "LIVE_TRADING_ENABLED",
        "MODEL_APPROVED",
        "RISK_GATE_ENABLED",
        "TRADINGVIEW_WEBHOOK_SECRET",
        "PAPER_INITIAL_CASH",
        "PAPER_FEE_BPS",
        "PAPER_SLIPPAGE_BPS",
        "PAPER_ACCOUNT_PATH",
        "PAPER_MAX_ORDER_NOTIONAL",
        "XGBOOST_MODEL_DIR",
        "CORS_ALLOWED_ORIGINS",
        "API_DOCS_ENABLED",
        "LOG_LEVEL",
        "DOTO_MT5_TERMINAL_PATH",
        "MT5_EXPECTED_LOGIN",
        "MT5_EXPECTED_SERVER",
        "MT5_DEMO_EXECUTION_ENABLED",
        "MT5_DEMO_EXPECTED_LOGIN",
        "MT5_DEMO_EXPECTED_SERVER",
    }

    assert expected <= declared
    assert "password" not in template.lower()
    assert "private_key" not in template.lower()


def test_production_template_defaults_keep_execution_disabled():
    template = (
        Path(__file__).resolve().parents[2] / "deploy" / "production.env.example"
    ).read_text(encoding="utf-8")

    assert "TRADING_MODE=simulation" in template
    assert "LIVE_TRADING_ENABLED=false" in template
    assert "MODEL_APPROVED=false" in template
    assert "MT5_DEMO_EXECUTION_ENABLED=false" in template
