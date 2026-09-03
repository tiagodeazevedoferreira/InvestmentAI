from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.services.mt5_demo import DemoBrokerError, MT5DemoBroker
from app.services.order_manager import OrderIntent


class FakeGateway:
    ORDER_TYPE_BUY = 0
    ORDER_TYPE_SELL = 1
    TRADE_ACTION_DEAL = 1
    ORDER_FILLING_IOC = 1
    TRADE_RETCODE_DONE = 10009

    def __init__(self, *, server="Doto-Demo", trade_allowed=True):
        self._account = {
            "login": 123,
            "server": server,
            "balance": 10000,
            "equity": 10100,
            "currency": "USD",
            "trade_allowed": trade_allowed,
        }
        self.requests = []

    def account_info(self):
        return self._account

    def symbol_info(self, symbol):
        return {"symbol": symbol, "last": 100.0, "ask": 100.1, "bid": 99.9}

    def positions_get(self):
        return [{"ticket": 10, "symbol": "PETR4", "volume": 2, "type": 0, "price_open": 90}]

    def orders_get(self):
        return [{"ticket": 20, "symbol": "PETR4", "volume_current": 1, "type": 2, "state": 1}]

    def history_deals_get(self, date_from, date_to):
        return [{"ticket": 30, "order": 20, "symbol": "PETR4", "volume": 1, "price": 100, "time": 123}]

    def order_check(self, request):
        self.requests.append(("check", request))
        return {"retcode": self.TRADE_RETCODE_DONE}

    def order_send(self, request):
        self.requests.append(("send", request))
        return {"retcode": self.TRADE_RETCODE_DONE, "order": 40, "deal": 41, "price": request["price"]}


def test_demo_account_is_normalized():
    account = MT5DemoBroker(FakeGateway()).account()
    assert account.server == "Doto-Demo"
    assert account.balance == 10000
    assert account.trade_allowed is True


def test_non_demo_server_is_rejected():
    with pytest.raises(DemoBrokerError, match="non-demo"):
        MT5DemoBroker(FakeGateway(server="Doto-Live")).account()


def test_positions_orders_and_executions_are_read_only_snapshots():
    broker = MT5DemoBroker(FakeGateway())
    assert broker.positions()[0]["symbol"] == "PETR4"
    assert broker.open_orders()[0]["order_id"] == "20"
    assert broker.executions(datetime(2026, 1, 1, tzinfo=timezone.utc), datetime(2026, 1, 2, tzinfo=timezone.utc))[0]["execution_id"] == "30"


def test_submit_requires_order_check_then_send():
    gateway = FakeGateway()
    result = MT5DemoBroker(gateway).submit(OrderIntent("PETR4", "BUY", 1))
    assert result["environment"] == "demo"
    assert result["order_id"] == "40"
    assert [kind for kind, _ in gateway.requests] == ["check", "send"]


def test_submit_rejects_account_without_trade_permission():
    with pytest.raises(DemoBrokerError, match="does not allow trading"):
        MT5DemoBroker(FakeGateway(trade_allowed=False)).submit(OrderIntent("PETR4", "BUY", 1))


def test_cancel_is_conservatively_blocked_until_semantics_are_validated():
    with pytest.raises(DemoBrokerError, match="not implemented"):
        MT5DemoBroker(FakeGateway()).cancel("20")
