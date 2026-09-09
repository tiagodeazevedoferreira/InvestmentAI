from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api import routes
from app.services.mt5_doto import DotoMT5ConnectionError


def test_mt5_status_returns_account_snapshot(monkeypatch):
    monkeypatch.setattr(routes, "settings", SimpleNamespace(
        mt5_terminal_path="C:\\DOTO\\terminal64.exe",
        mt5_expected_login=5344431,
        mt5_expected_server="DOTOGlobal-Real",
    ))

    class Gateway:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
        def connect(self):
            return SimpleNamespace(
                login=5344431, server="DOTOGlobal-Real",
                company="DOTO Global Ltd", currency="BRL",
                balance=52000.0, equity=52000.0,
                trade_allowed=True, trade_expert=True,
            )
        def close(self):
            pass

    monkeypatch.setattr(routes, "MetaTrader5DotoGateway", Gateway)
    assert routes.mt5_status() == {
        "connected": True, "login": 5344431,
        "server": "DOTOGlobal-Real", "company": "DOTO Global Ltd",
        "currency": "BRL", "balance": 52000.0, "equity": 52000.0,
        "trade_allowed": True, "trade_expert": True,
    }


def test_mt5_status_requires_terminal_path(monkeypatch):
    monkeypatch.setattr(routes, "settings", SimpleNamespace(
        mt5_terminal_path=None, mt5_expected_login=5344431,
        mt5_expected_server="DOTOGlobal-Real",
    ))
    with pytest.raises(HTTPException) as exc_info:
        routes.mt5_status()
    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "MT5 terminal path is not configured"


def test_mt5_status_maps_connection_error_to_503(monkeypatch):
    monkeypatch.setattr(routes, "settings", SimpleNamespace(
        mt5_terminal_path="C:\\DOTO\\terminal64.exe",
        mt5_expected_login=5344431,
        mt5_expected_server="DOTOGlobal-Real",
    ))

    class FailingGateway:
        def __init__(self, **kwargs):
            pass
        def connect(self):
            raise DotoMT5ConnectionError("MT5 initialize failed")
        def close(self):
            pass

    monkeypatch.setattr(routes, "MetaTrader5DotoGateway", FailingGateway)
    with pytest.raises(HTTPException) as exc_info:
        routes.mt5_status()
    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "MT5 initialize failed"
