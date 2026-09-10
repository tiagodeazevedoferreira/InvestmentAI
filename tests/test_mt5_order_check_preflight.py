from types import SimpleNamespace

import pytest

from scripts.check_doto_mt5_order import OrderCheckBlocked, build_request, run_order_check


class FakeMT5:
    ORDER_TYPE_BUY = 0
    ORDER_TYPE_SELL = 1
    TRADE_ACTION_DEAL = 1
    ORDER_TIME_GTC = 0
    ORDER_FILLING_IOC = 1

    def __init__(self):
        self.checked = []
        self.sent = []

    def terminal_info(self):
        return SimpleNamespace(connected=True)

    def account_info(self):
        return SimpleNamespace(
            login=5344431,
            server="DOTOGlobal-Real",
            trade_allowed=True,
            trade_expert=True,
        )

    def symbol_select(self, symbol, selected):
        return selected

    def symbol_info(self, symbol):
        return SimpleNamespace(volume_min=0.001, volume_max=100.0, volume_step=0.01)

    def symbol_info_tick(self, symbol):
        return SimpleNamespace(bid=100.0, ask=101.0)

    def order_check(self, request):
        self.checked.append(request)
        return SimpleNamespace(retcode=0, comment="OK")

    def order_send(self, request):
        self.sent.append(request)
        raise AssertionError("order_send must never be called by the preflight")


def test_order_check_preflight_validates_and_never_sends():
    mt5 = FakeMT5()
    result = run_order_check(
        mt5,
        expected_login=5344431,
        expected_server="DOTOGlobal-Real",
        symbol="eurusd",
        side="BUY",
        volume=0.01,
    )

    assert result["symbol"] == "EURUSD"
    assert result["volume"] == 0.01
    assert result["retcode"] == 0
    assert result["order_send_called"] is False
    assert len(mt5.checked) == 1
    assert mt5.sent == []
    assert mt5.checked[0]["comment"] == "InvestmentAI-DEMO-PREFLIGHT"


def test_order_check_preflight_rejects_wrong_account():
    mt5 = FakeMT5()
    with pytest.raises(OrderCheckBlocked, match="account mismatch"):
        run_order_check(
            mt5,
            expected_login=999999,
            expected_server="DOTOGlobal-Real",
            symbol="EURUSD",
            side="BUY",
            volume=0.01,
        )
    assert mt5.checked == []


def test_build_request_rejects_volume_above_controlled_limit():
    mt5 = FakeMT5()
    with pytest.raises(OrderCheckBlocked, match="volume must be"):
        build_request(mt5, symbol="EURUSD", side="BUY", volume=0.02)


def test_build_request_rejects_step_mismatch():
    mt5 = FakeMT5()
    with pytest.raises(OrderCheckBlocked, match="not aligned"):
        build_request(mt5, symbol="EURUSD", side="BUY", volume=0.005)
