import pytest

from backend.app.services.paper_execution import PaperAccount, PaperExecutionError


def test_market_buy_mark_to_market_and_sell():
    account = PaperAccount(initial_cash=100_000, fee_bps=0, slippage_bps=0)

    buy = account.submit_order("PETR4", "BUY", 10, 40.0)
    assert buy["status"] == "filled"
    assert account.cash == 99_600
    assert account.positions["PETR4"].quantity == 10

    account.mark_to_market({"PETR4": 45.0})
    assert account.market_value == 450
    assert account.unrealized_pnl == 50
    assert account.equity == 100_050

    sell = account.submit_order("PETR4", "SELL", 10, 45.0)
    assert sell["status"] == "filled"
    assert account.cash == 100_050
    assert account.realized_pnl == 50
    assert account.positions == {}


def test_fees_and_slippage_are_accounted_for():
    account = PaperAccount(initial_cash=1_000, fee_bps=10, slippage_bps=10)
    result = account.submit_order("VALE3", "BUY", 2, 100.0)

    assert result["execution"]["fill_price"] == pytest.approx(100.1)
    assert result["execution"]["fee"] == pytest.approx(0.2002)
    assert account.cash == pytest.approx(799.5998)


def test_limit_order_waits_then_fills_on_mark():
    account = PaperAccount(initial_cash=1_000, fee_bps=0, slippage_bps=0)
    result = account.submit_order("ITUB4", "BUY", 5, 25.0, "LIMIT", 24.0)

    assert result["status"] == "open"
    assert len(account.positions) == 0

    account.mark_to_market({"ITUB4": 24.5})
    assert account.orders[0]["status"] == "open"

    account.mark_to_market({"ITUB4": 24.0})
    assert account.orders[0]["status"] == "filled"
    assert account.positions["ITUB4"].quantity == 5


def test_cannot_sell_more_than_position():
    account = PaperAccount(initial_cash=1_000, fee_bps=0, slippage_bps=0)
    with pytest.raises(PaperExecutionError, match="insufficient paper position"):
        account.submit_order("PETR4", "SELL", 1, 40.0)


def test_invalid_order_is_rejected():
    account = PaperAccount()
    with pytest.raises(ValueError, match="order_type"):
        account.submit_order("PETR4", "BUY", 1, 40.0, "STOP")
