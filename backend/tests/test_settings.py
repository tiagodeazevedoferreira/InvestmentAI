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
