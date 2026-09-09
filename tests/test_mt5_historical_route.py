from types import SimpleNamespace

from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.api import routes
from app.services.mt5_historical_data import MT5Candle


class FakeGateway:
    def __init__(self, **kwargs):
        self.closed = False
        self.kwargs = kwargs

    def connect(self):
        return None

    def candles(self, symbol, timeframe, count=100, start_pos=0):
        assert symbol == "EURUSD"
        assert timeframe == "M15"
        assert count == 2
        assert start_pos == 1
        return [
            MT5Candle(
                symbol="EURUSD",
                timeframe="M15",
                time=1788987600,
                timestamp="2026-09-09T21:00:00+00:00",
                open=1.16376,
                high=1.16389,
                low=1.16366,
                close=1.16375,
                tick_volume=369,
                spread=14,
                real_volume=0,
            ),
            MT5Candle(
                symbol="EURUSD",
                timeframe="M15",
                time=1788988500,
                timestamp="2026-09-09T21:15:00+00:00",
                open=1.16375,
                high=1.16375,
                low=1.16343,
                close=1.16351,
                tick_volume=258,
                spread=14,
                real_volume=0,
            ),
        ]

    def close(self):
        self.closed = True


def test_mt5_historical_candles_returns_candles(monkeypatch):
    monkeypatch.setattr(routes.settings, "mt5_terminal_path", "C:/DOTO/terminal64.exe")
    monkeypatch.setattr(routes.settings, "mt5_expected_login", 5344431)
    monkeypatch.setattr(routes.settings, "mt5_expected_server", "DOTOGlobal-Real")
    monkeypatch.setattr(routes, "MetaTrader5HistoricalDataGateway", FakeGateway)

    client = TestClient(app)
    response = client.get(
        "/api/market/mt5/EURUSD/candles?timeframe=M15&count=2&start_pos=1"
    )

    assert response.status_code == 200
    data = response.json()

    assert data["symbol"] == "EURUSD"
    assert data["timeframe"] == "M15"
    assert data["count"] == 2
    assert data["start_pos"] == 1
    assert data["candles"][0]["timestamp"] == "2026-09-09T21:00:00+00:00"
    assert data["candles"][0]["open"] == pytest.approx(1.16376)
    assert data["candles"][0]["high"] == pytest.approx(1.16389)
    assert data["candles"][0]["low"] == pytest.approx(1.16366)
    assert data["candles"][0]["close"] == pytest.approx(1.16375)
    assert data["candles"][0]["tick_volume"] == 369
    assert data["candles"][0]["spread"] == 14
    assert data["candles"][0]["real_volume"] == 0


def test_mt5_historical_candles_requires_terminal_path(monkeypatch):
    monkeypatch.setattr(routes.settings, "mt5_terminal_path", None)

    client = TestClient(app)
    response = client.get("/api/market/mt5/EURUSD/candles")

    assert response.status_code == 503
    assert response.json()["detail"] == "MT5 terminal path is not configured"


def test_mt5_historical_candles_maps_gateway_error(monkeypatch):
    monkeypatch.setattr(routes.settings, "mt5_terminal_path", "C:/DOTO/terminal64.exe")

    class ErrorGateway:
        def __init__(self, **kwargs):
            pass

        def candles(self, *args, **kwargs):
            raise routes.MT5HistoricalDataError("Unable to retrieve candles")

        def close(self):
            pass

    monkeypatch.setattr(routes, "MetaTrader5HistoricalDataGateway", ErrorGateway)

    client = TestClient(app)
    response = client.get("/api/market/mt5/EURUSD/candles")

    assert response.status_code == 503
    assert response.json()["detail"] == "Unable to retrieve candles"


def test_mt5_historical_candles_validates_query_parameters(monkeypatch):
    monkeypatch.setattr(routes.settings, "mt5_terminal_path", "C:/DOTO/terminal64.exe")
    monkeypatch.setattr(routes, "MetaTrader5HistoricalDataGateway", FakeGateway)

    client = TestClient(app)

    assert client.get("/api/market/mt5/EURUSD/candles?count=0").status_code == 422
    assert client.get("/api/market/mt5/EURUSD/candles?count=5001").status_code == 422
    assert client.get("/api/market/mt5/EURUSD/candles?start_pos=-1").status_code == 422
