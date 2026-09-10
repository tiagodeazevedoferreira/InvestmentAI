from datetime import datetime, timezone

import pytest

from app.services.mt5_demo_broker import MT5DemoExecutionError, MetaTrader5DemoBroker
from app.services.order_manager import OrderIntent


class FakeMT5:
    ORDER_TYPE_BUY = 0
    ORDER_TYPE_SELL = 1
    TRADE_ACTION_DEAL = 1
    ORDER_TIME_GTC = 0
    ORDER_FILLING_IOC = 1
    TRADE_RETCODE_DONE = 10009
    TRADE_RETCODE_PLACED = 10008

    def __init__(self, check_retcode=0):
        self.check_retcode = check_retcode
        self.calls = []

    def initialize(self, **kwargs):
        self.calls.append(("initialize", kwargs))
        return True

    def terminal_info(self):
        return {"connected": True}

    def account_info(self):
        return {
            "login": 123456,
            "server": "DOTOGlobal-Demo",
            "balance": 10000.0,
            "equity": 10000.0,
            "currency": "USD",
            "trade_allowed": True,
            "trade_expert": True,
        }

    def positions_get(self):
        return []

    def orders_get(self):
        return []

    def history_deals_get(self, date_from, date_to):
        return []

    def symbol_select(self, symbol, enabled):
        return True

    def symbol_info(self, symbol):
        return {"symbol": symbol}

    def symbol_info_tick(self, symbol):
        return {"ask": 100.1, "bid": 99.9}

    def order_check(self, request):
        self.calls.append(("check", request))
        return {"retcode": self.check_retcode}

    def order_send(self, request):
        self.calls.append(("send", request))
        return {"retcode": self.TRADE_RETCODE_DONE, "order": 40, "deal": 41, "volume": request["volume"]}

    def last_error(self):
        return (1, "Success")

    def shutdown(self):
        self.calls.append(("shutdown", {}))


def _broker(mt5, enabled=True):
    broker = MetaTrader5DemoBroker(
        terminal_path="C:/DOTO/terminal64.exe",
        expected_login=123456,
        expected_server="DOTOGlobal-Demo",
        mt5_module=mt5,
        execution_enabled=enabled,
    )
    broker.connect()
    return broker


def test_reconciliation_snapshot_matches_executor_protocol():
    broker = _broker(FakeMT5())
    snapshot = broker.reconciliation_snapshot(
        datetime(2026, 9, 10, 12, 0, tzinfo=timezone.utc),
        datetime(2026, 9, 10, 12, 5, tzinfo=timezone.utc),
    )
    assert snapshot["cash"] == 10000.0
    assert snapshot["equity"] == 10000.0
    assert snapshot["positions"] == {}
    assert snapshot["open_orders"] == []
    assert snapshot["executions"] == []
    assert snapshot["captured_at"]


def test_submit_runs_order_check_before_send():
    mt5 = FakeMT5()
    broker = _broker(mt5)
    result = broker.submit(OrderIntent("EURUSD", "BUY", 0.01))
    assert result["accepted"] is True
    assert [call[0] for call in mt5.calls if call[0] in {"check", "send"}] == ["check", "send"]


def test_failed_order_check_blocks_order_send():
    mt5 = FakeMT5(check_retcode=10019)
    broker = _broker(mt5)
    with pytest.raises(MT5DemoExecutionError, match="order_check rejected"):
        broker.submit(OrderIntent("EURUSD", "BUY", 0.01))
    assert not any(call[0] == "send" for call in mt5.calls)


def test_disabled_execution_remains_fail_closed():
    broker = _broker(FakeMT5(), enabled=False)
    with pytest.raises(MT5DemoExecutionError, match="execution is disabled"):
        broker.submit(OrderIntent("EURUSD", "BUY", 0.01))
