from types import SimpleNamespace

from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.api import routes
from app.services.mt5_market_data import MT5Quote


class FakeGateway:
    def __init__(self, **kwargs):
        self.closed = False
        self.kwargs = kwargs

    def connect(self):
        return None

    def quote(self, symbol):
        assert symbol == "EURUSD"
        return MT5Quote(
            symbol="EURUSD",
            bid=1.16280,
            ask=1.16294,
            last=0.0,
            time=1788990888,
            time_msc=1788990888424,
        )

    def close(self):
        self.closed = True


def test_mt5_market_returns_quote(monkeypatch):
    monkeypatch.setattr(routes.settings, "mt5_terminal_path", "C:/DOTO/terminal64.exe")
    monkeypatch.setattr(routes.settings, "mt5_expected_login", 5344431)
    monkeypatch.setattr(routes.settings, "mt5_expected_server", "DOTOGlobal-Real")
    monkeypatch.setattr(routes, "MetaTrader5MarketDataGateway", FakeGateway)

    client = TestClient(app)
    response = client.get("/api/market/mt5/EURUSD")

    assert response.status_code == 200

    data = response.json()

    assert data["symbol"] == "EURUSD"
    assert data["bid"] == pytest.approx(1.16280)
    assert data["ask"] == pytest.approx(1.16294)
    assert data["last"] == pytest.approx(0.0)
    assert data["spread"] == pytest.approx(0.00014)
    assert data["time"] == 1788990888
    assert data["time_msc"] == 1788990888424
    assert data["timestamp"] == "2026-09-09T21:54:48+00:00"


def test_mt5_market_requires_terminal_path(monkeypatch):
    monkeypatch.setattr(routes.settings, "mt5_terminal_path", None)

    client = TestClient(app)
    response = client.get("/api/market/mt5/EURUSD")

    assert response.status_code == 503
    assert response.json()["detail"] == "MT5 terminal path is not configured"


def test_mt5_market_maps_gateway_error(monkeypatch):
    monkeypatch.setattr(routes.settings, "mt5_terminal_path", "C:/DOTO/terminal64.exe")

    class ErrorGateway:
        def __init__(self, **kwargs):
            pass

        def connect(self):
            raise routes.MT5MarketDataError("Unexpected MT5 server")

        def close(self):
            pass

    monkeypatch.setattr(routes, "MetaTrader5MarketDataGateway", ErrorGateway)

    client = TestClient(app)
    response = client.get("/api/market/mt5/EURUSD")

    assert response.status_code == 503
    assert response.json()["detail"] == "Unexpected MT5 server"
