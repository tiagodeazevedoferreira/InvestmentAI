from __future__ import annotations

import pytest

from app.services.mt5_doto import DotoMT5ConnectionError, MetaTrader5DotoGateway


class FakeMT5:
    def __init__(self, *, account=None, terminal=None, initialize_result=True):
        self.account = account
        self.terminal = terminal
        self.initialize_result = initialize_result
        self.initialize_calls = []
        self.shutdown_called = False

    def initialize(self, **kwargs):
        self.initialize_calls.append(kwargs)
        return self.initialize_result

    def shutdown(self):
        self.shutdown_called = True

    def last_error(self):
        return (-6, "Terminal: Authorization failed")

    def terminal_info(self):
        return self.terminal

    def account_info(self):
        return self.account


def account(**overrides):
    values = {
        "login": 5344431,
        "server": "DOTOGlobal-Real",
        "company": "DOTO Global Ltd",
        "currency": "BRL",
        "balance": 52000.0,
        "equity": 52000.0,
        "trade_allowed": True,
        "trade_expert": True,
    }
    values.update(overrides)
    return values


def test_connect_uses_doto_terminal_path_and_verifies_account():
    mt5 = FakeMT5(account=account(), terminal={"connected": True})
    gateway = MetaTrader5DotoGateway(
        terminal_path=r"C:\Users\tiago.ferreira\AppData\Roaming\DOTO Global MT5 Terminal\terminal64.exe",
        expected_login=5344431,
        mt5_module=mt5,
    )

    snapshot = gateway.connect()

    assert mt5.initialize_calls == [
        {
            "path": r"C:\Users\tiago.ferreira\AppData\Roaming\DOTO Global MT5 Terminal\terminal64.exe",
            "timeout": 60000,
        }
    ]
    assert snapshot.login == 5344431
    assert snapshot.server == "DOTOGlobal-Real"
    assert snapshot.company == "DOTO Global Ltd"
    assert snapshot.balance == 52000.0
    assert snapshot.trade_allowed is True


def test_connect_rejects_wrong_account():
    mt5 = FakeMT5(account=account(login=123), terminal={"connected": True})
    gateway = MetaTrader5DotoGateway(
        terminal_path="doto-terminal64.exe",
        expected_login=5344431,
        mt5_module=mt5,
    )

    with pytest.raises(DotoMT5ConnectionError, match="Unexpected MT5 account"):
        gateway.connect()

    assert mt5.shutdown_called is True


def test_connect_rejects_wrong_server():
    mt5 = FakeMT5(account=account(server="MetaQuotes-Demo"), terminal={"connected": True})
    gateway = MetaTrader5DotoGateway(
        terminal_path="doto-terminal64.exe",
        expected_login=5344431,
        mt5_module=mt5,
    )

    with pytest.raises(DotoMT5ConnectionError, match="Unexpected MT5 server"):
        gateway.connect()

    assert mt5.shutdown_called is True


def test_connect_rejects_disconnected_terminal():
    mt5 = FakeMT5(account=account(), terminal={"connected": False})
    gateway = MetaTrader5DotoGateway(
        terminal_path="doto-terminal64.exe",
        expected_login=5344431,
        mt5_module=mt5,
    )

    with pytest.raises(DotoMT5ConnectionError, match="not connected"):
        gateway.connect()


def test_connect_surfaces_initialize_error():
    mt5 = FakeMT5(account=None, terminal=None, initialize_result=False)
    gateway = MetaTrader5DotoGateway(
        terminal_path="doto-terminal64.exe",
        mt5_module=mt5,
    )

    with pytest.raises(DotoMT5ConnectionError, match="Authorization failed"):
        gateway.connect()


def test_close_shuts_down_after_successful_connection():
    mt5 = FakeMT5(account=account(), terminal={"connected": True})
    gateway = MetaTrader5DotoGateway(
        terminal_path="doto-terminal64.exe",
        mt5_module=mt5,
    )

    gateway.connect()
    gateway.close()

    assert mt5.shutdown_called is True
