from app.settings import Settings


def test_mt5_terminal_path_reads_doto_environment_variable(monkeypatch):
    monkeypatch.setenv("DOTO_MT5_TERMINAL_PATH", r"C:\Doto\terminal64.exe")
    monkeypatch.delenv("MT5_TERMINAL_PATH", raising=False)

    settings = Settings()

    assert settings.mt5_terminal_path == r"C:\Doto\terminal64.exe"


def test_mt5_terminal_path_keeps_legacy_environment_variable(monkeypatch):
    monkeypatch.delenv("DOTO_MT5_TERMINAL_PATH", raising=False)
    monkeypatch.setenv("MT5_TERMINAL_PATH", r"C:\Legacy\terminal64.exe")

    settings = Settings()

    assert settings.mt5_terminal_path == r"C:\Legacy\terminal64.exe"


def test_production_api_security_settings(monkeypatch):
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://app.example, https://admin.example")
    monkeypatch.setenv("API_DOCS_ENABLED", "false")

    settings = Settings()
    assert settings.cors_allowed_origins == "https://app.example, https://admin.example"
    assert settings.api_docs_enabled is False


def test_log_level_reads_environment_variable(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "debug")

    settings = Settings()

    assert settings.log_level == "debug"


def test_cors_origin_parser_ignores_empty_entries():
    from app.main import _cors_origins

    assert _cors_origins(" https://app.example, ,https://admin.example ") == ["https://app.example", "https://admin.example"]
    assert _cors_origins("") == ["*"]
