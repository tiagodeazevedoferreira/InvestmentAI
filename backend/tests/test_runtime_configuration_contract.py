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


def test_production_persistence_contract_keeps_durable_state_out_of_ephemeral_container_storage():
    root = Path(__file__).resolve().parents[2]
    persistence = (root / "docs" / "codex" / "tasks" / "045-production-persistence-contract.md").read_text(
        encoding="utf-8"
    )
    paper_store = (root / "backend" / "app" / "services" / "paper_store.py").read_text(encoding="utf-8")
    paper_ledger = (root / "backend" / "app" / "services" / "paper_ledger.py").read_text(encoding="utf-8")
    demo_ledger = (root / "backend" / "app" / "services" / "demo_ledger.py").read_text(encoding="utf-8")

    assert "PAPER account" in persistence
    assert "Firebase Realtime Database" in persistence
    assert "DEMO order ledger" in persistence
    assert "Windows execution workstation" in persistence
    assert "models/xgboost" in persistence
    assert "self.firebase.get(self.path)" in paper_store
    assert "Firebase is required for paper idempotency" in paper_ledger
    assert "sqlite3" in demo_ledger


def test_backup_recovery_contract_preserves_execution_safety_boundaries():
    root = Path(__file__).resolve().parents[2]
    contract = (root / "docs" / "codex" / "tasks" / "046-backup-recovery-contract.md").read_text(
        encoding="utf-8"
    )

    required_phrases = (
        "paper/decision_ledger",
        "paper/shadow_decision_ledger",
        "SUBMITTED",
        "never trigger automatic broker resubmission",
        "XGBOOST_MODEL_DIR",
        "fail model-dependent readiness/inference",
        "No new DEMO transaction is required",
    )
    for phrase in required_phrases:
        assert phrase in contract


def test_production_hosting_contract_preserves_linux_windows_execution_boundary():
    root = Path(__file__).resolve().parents[2]
    contract = (
        root / "docs" / "codex" / "tasks" / "047-production-hosting-deployment-contract.md"
    ).read_text(encoding="utf-8")
    dockerfile = (root / "Dockerfile").read_text(encoding="utf-8")
    runtime_template = (root / "deploy" / "production.env.example").read_text(encoding="utf-8")
    architecture = (root / "ARCHITECTURE.md").read_text(encoding="utf-8")

    required_phrases = (
        "Linux production runtime",
        "Windows DOTO/MT5 execution boundary",
        "TLS termination",
        "GET /api/health",
        "GET /api/ready",
        "PAPER authoritative state remains external",
        "DEMO SQLite state remains on the controlled Windows workstation",
        "No automatic model promotion",
    )
    for phrase in required_phrases:
        assert phrase in contract

    assert "terminal64.exe" not in dockerfile
    assert "mt5" not in dockerfile.lower()
    assert "TRADING_MODE=simulation" in runtime_template
    assert "LIVE_TRADING_ENABLED=false" in runtime_template
    assert "MT5_DEMO_EXECUTION_ENABLED=false" in runtime_template
    assert "Prediction never directly places an order." in architecture
