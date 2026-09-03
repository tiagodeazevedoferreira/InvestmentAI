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
