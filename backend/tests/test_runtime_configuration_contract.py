from pathlib import Path

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
    assert "password=" not in template.lower()
    assert "private_key=" not in template.lower()


def test_production_template_defaults_keep_execution_disabled():
    template = (
        Path(__file__).resolve().parents[2] / "deploy" / "production.env.example"
    ).read_text(encoding="utf-8")

    assert "TRADING_MODE=simulation" in template
    assert "LIVE_TRADING_ENABLED=false" in template
    assert "MODEL_APPROVED=false" in template
    assert "MT5_DEMO_EXECUTION_ENABLED=false" in template

def test_secret_values_are_runtime_only():
    root = Path(__file__).resolve().parents[2]
    template = (root / "deploy" / "production.env.example").read_text(encoding="utf-8")
    dockerfile = (root / "Dockerfile").read_text(encoding="utf-8")
    dockerignore = (root / ".dockerignore").read_text(encoding="utf-8")

    for key in ("FIREBASE_SERVICE_ACCOUNT", "TRADINGVIEW_WEBHOOK_SECRET"):
        assert f"{key}=" in template
        assert f"{key}=\n" in template

    assert "ARG FIREBASE_SERVICE_ACCOUNT" not in dockerfile
    assert "ARG TRADINGVIEW_WEBHOOK_SECRET" not in dockerfile
    assert ".env" in dockerignore
    assert ".env.*" in dockerignore


def test_secret_bearing_webhook_routes_are_logged_without_path_values():
    main = (Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(
        encoding="utf-8"
    )

    assert "def _request_route(request: Request)" in main
    assert "_request_route(request)" in main
    assert "logger.info(" in main
    assert "logger.exception(" in main
