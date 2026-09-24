from __future__ import annotations

import pytest

from app.services.historical_statements import normalize_historical_statements


def test_normalizes_provider_aliases_and_orders_periods():
    records = [
        {"asOfDate": "2025-12-31", "totalRevenue": 120.0, "netIncomeToCommon": 12.0, "totalDebt": 30.0},
        {"date": "2024-12-31", "revenue": 100.0, "net_income": 10.0, "equity": 50.0},
    ]

    result = normalize_historical_statements(records, symbol="PETR4.SA", statement_type="Annual")

    assert [item.period_end for item in result] == ["2024-12-31", "2025-12-31"]
    assert result[0].symbol == "PETR4"
    assert result[1].revenue == 120.0
    assert result[1].net_income == 12.0
    assert result[1].total_debt == 30.0


def test_missing_period_fails_closed():
    with pytest.raises(ValueError, match="period_end"):
        normalize_historical_statements([{"revenue": 100}], symbol="PETR4", statement_type="annual")


def test_non_finite_value_fails_closed():
    with pytest.raises(ValueError, match="finite"):
        normalize_historical_statements(
            [{"period_end": "2025-12-31", "revenue": float("nan")}],
            symbol="PETR4",
            statement_type="annual",
        )


def test_empty_input_is_valid_but_contains_no_statements():
    assert normalize_historical_statements([], symbol="PETR4", statement_type="annual") == ()
