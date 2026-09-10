from types import SimpleNamespace

import pytest

from backend.app.services.mt5_demo_broker import MT5DemoExecutionError, MetaTrader5DemoBroker
from backend.app.services.order_manager import OrderIntent


class FakeMT5:
    ORDER_TYPE_BUY = 0
    ORDER_TYPE_SELL = 1
    TRADE_ACTION_DEAL = 1
    ORDER_TIME_GTC = 0
    ORDER_FILLING_IOC = 1
    TRADE_RETCODE_DONE = 10009
    TRADE_RETCODE_PLACED = 10008

    def __init__(self, login=123456, server="Demo-Server"):
        self.login = login
        self.server = server
        self.sent = []
        self.shutdown_called = False

    def initialize(self, **kwargs):
        return True

    def last_error(self):
        return (1, "Success")

    def terminal_info(self):
        return SimpleNamespace(connected=True)

    def account_info(self):
        return SimpleNamespace(login=self.login, server=self.server, balance=100000.0, equity=100000.0, currency="USD", trade_allowed=True, trade_expert=True)

    def symbol_select(self, symbol, selected):
        return selected

    def symbol_info(self, symbol):
        return SimpleNamespace(volume_min=0.01)

    def symbol_info_tick(self, symbol):
        return SimpleNamespace(bid=100.0, ask=101.0)

    def order_send(self, request):
        self.sent.append(request)
        return SimpleNamespace(retcode=self.TRADE_RETCODE_DONE, order=77, deal=88, volume=request["volume"])

    def shutdown(self):
        self.shutdown_called = True


def make_broker(mt5, enabled=False):
    return MetaTrader5DemoBroker(terminal_path="terminal64.exe", expected_login=123456, expected_server="Demo-Server", mt5_module=mt5, execution_enabled=enabled)


def test_connect_rejects_wrong_demo_server():
    broker = MetaTrader5DemoBroker(terminal_path="terminal64.exe", expected_login=123456, expected_server="DOTOGlobal-Demo", mt5_module=FakeMT5(server="DOTOGlobal-Real"))
    with pytest.raises(MT5DemoExecutionError, match="DEMO server mismatch"):
        broker.connect()


def test_submit_is_disabled_by_default_even_when_connected():
    mt5 = FakeMT5()
    broker = make_broker(mt5)
    broker.connect()
    with pytest.raises(MT5DemoExecutionError, match="execution is disabled"):
        broker.submit(OrderIntent("EURUSD", "BUY", 0.01))
    assert mt5.sent == []


def test_submit_sends_only_after_explicit_demo_enablement():
    mt5 = FakeMT5()
    broker = make_broker(mt5, enabled=True)
    broker.connect()
    result = broker.submit(OrderIntent("EURUSD", "BUY", 0.01))
    assert result["accepted"] is True
    assert result["environment"] == "demo"
    assert len(mt5.sent) == 1
    assert mt5.sent[0]["comment"] == "InvestmentAI-DEMO"
