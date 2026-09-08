from types import SimpleNamespace

import pytest

from backend.app.services.mt5_demo import DemoBrokerError, MT5DemoBroker
from backend.app.services.order_manager import OrderIntent


class Gateway:
    def __init__(self, *, check_retcode=0):
        self.check_retcode = check_retcode
        self.check_requests = []

    def account_info(self):
        return SimpleNamespace(server="DOTOGlobal-Demo", trade_allowed=True, trade_mode=0)

    def symbol_info(self, symbol):
        return SimpleNamespace(symbol=symbol, bid=10.0, ask=10.2)

    def order_check(self, request):
        self.check_requests.append(request)
        return SimpleNamespace(retcode=self.check_retcode, comment="ok")


def test_prepare_market_order_uses_ask_for_buy_without_sending():
    gateway = Gateway()
    broker = MT5DemoBroker(gateway)
    request = broker.prepare_market_order(OrderIntent("PETR4", "BUY", 10))

    assert request["price"] == 10.2
    assert gateway.check_requests == []


def test_prepare_market_order_uses_bid_for_sell_without_sending():
    gateway = Gateway()
    broker = MT5DemoBroker(gateway)
    request = broker.prepare_market_order(OrderIntent("PETR4", "SELL", 10))

    assert request["price"] == 10.0
    assert gateway.check_requests == []


def test_check_order_is_non_submitting_and_accepts_zero_retcode():
    gateway = Gateway(check_retcode=0)
    broker = MT5DemoBroker(gateway)
    request = broker.prepare_market_order(OrderIntent("PETR4", "BUY", 1))

    result = broker.check_order(request)

    assert result["retcode"] == 0
    assert len(gateway.check_requests) == 1


def test_check_order_rejects_nonzero_retcode():
    gateway = Gateway(check_retcode=10019)
    broker = MT5DemoBroker(gateway)
    request = broker.prepare_market_order(OrderIntent("PETR4", "BUY", 1))

    with pytest.raises(DemoBrokerError, match="order_check rejected"):
        broker.check_order(request)


def test_prepare_rejects_limit_order_until_pending_semantics_exist():
    broker = MT5DemoBroker(Gateway())

    with pytest.raises(DemoBrokerError, match="limit_price is unsupported"):
        broker.prepare_market_order(OrderIntent("PETR4", "BUY", 1, limit_price=9.9))
