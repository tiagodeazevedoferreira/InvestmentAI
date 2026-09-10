import pytest
from types import SimpleNamespace

from backend.app.services.mt5_demo_broker import MT5DemoExecutionError, MetaTrader5DemoBroker
from backend.app.services.order_manager import OrderIntent


class FakeMT5:
    ORDER_TYPE_BUY = 0
    ORDER_TYPE_SELL = 1
    TRADE_ACTION_DEAL = 1
    ORDER_TIME_GTC = 0
    ORDER_FILLING_IOC = 1
    TRADE_RETCODE_DONE = 10009
    def initialize(self, **kwargs): return True
    def last_error(self): return (1, "Success")
    def terminal_info(self): return SimpleNamespace(connected=True)
    def account_info(self): return SimpleNamespace(login=1, server="Demo", balance=1000, equity=1000, currency="USD", trade_allowed=True, trade_expert=True)
    def symbol_select(self, symbol, selected): return True
    def symbol_info(self, symbol): return SimpleNamespace(volume_min=0.01, volume_max=100)
    def symbol_info_tick(self, symbol): return SimpleNamespace(bid=100, ask=101)
    def order_send(self, request): return SimpleNamespace(retcode=10009, order=1, deal=1, volume=request["volume"])
    def shutdown(self): pass


def test_demo_volume_above_safety_limit_is_blocked():
    broker = MetaTrader5DemoBroker(terminal_path="terminal64.exe", expected_login=1, expected_server="Demo", mt5_module=FakeMT5(), execution_enabled=True)
    broker.connect()
    with pytest.raises(MT5DemoExecutionError, match="safety limit"):
        broker.submit(OrderIntent("EURUSD", "BUY", 0.02))
