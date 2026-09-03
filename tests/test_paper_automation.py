import pandas as pd

from backend.app.services.paper_automation import evaluate_paper_signal
from backend.app.services.paper_execution import PaperAccount


def bars(values):
    return pd.DataFrame({
        "Open": values,
        "High": [v + 0.5 for v in values],
        "Low": [v - 0.5 for v in values],
        "Close": values,
        "Volume": [1000.0] * len(values),
    })


def test_oversold_signal_is_sized_and_executed_in_paper():
    account = PaperAccount(initial_cash=100_000, fee_bps=0, slippage_bps=0)
    result = evaluate_paper_signal(
        account, "PETR4", bars(list(range(60, 29, -1))), max_order_notional=10_000, target_allocation=0.05
    )
    assert result["decision"]["action"] == "BUY"
    assert result["decision"]["risk_allowed"] is True
    assert result["executed"] is True
    assert account.positions["PETR4"].quantity == 166
    assert account.positions["PETR4"].average_price == 30


def test_sell_signal_without_position_is_blocked_by_risk_gate():
    account = PaperAccount(initial_cash=100_000, fee_bps=0, slippage_bps=0)
    result = evaluate_paper_signal(
        account, "VALE3", bars(list(range(30, 61))), max_order_notional=10_000
    )
    assert result["decision"]["action"] == "SELL"
    assert result["decision"]["risk_allowed"] is False
    assert result["executed"] is False


def test_hold_never_creates_order():
    account = PaperAccount(initial_cash=100_000, fee_bps=0, slippage_bps=0)
    values = [100 + ((i % 2) * 0.1) for i in range(30)]
    result = evaluate_paper_signal(account, "ITUB4", bars(values))
    assert result["decision"]["action"] == "HOLD"
    assert result["executed"] is False
    assert account.orders == []


def test_client_order_id_prevents_duplicate_paper_fill():
    account = PaperAccount(initial_cash=100_000, fee_bps=0, slippage_bps=0)
    first = account.submit_order("PETR4", "BUY", 100, 30, client_order_id="paper-signal-1")
    second = account.submit_order("PETR4", "BUY", 100, 30, client_order_id="paper-signal-1")
    assert first["order_id"] == second["order_id"]
    assert account.positions["PETR4"].quantity == 100
    assert len(account.orders) == 1
    assert len(account.executions) == 1


def test_buy_sizing_does_not_accumulate_above_target_allocation():
    account = PaperAccount(initial_cash=100_000, fee_bps=0, slippage_bps=0)
    market = bars(list(range(60, 29, -1)))
    first = evaluate_paper_signal(account, "PETR4", market, max_order_notional=10_000, target_allocation=0.05)
    second = evaluate_paper_signal(account, "PETR4", market, max_order_notional=10_000, target_allocation=0.05)
    assert first["executed"] is True
    assert second["executed"] is False
    assert second["decision"]["risk_allowed"] is False
    assert account.positions["PETR4"].quantity == 166
