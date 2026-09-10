import pytest

from app.services.demo_order_preflight import DemoOrderPreflight, DemoOrderPreflightError
from app.services.order_manager import OrderIntent


def _state():
    return {"cash": 1000.0, "positions": {}, "open_orders": [], "executions": []}


def test_normalizes_controlled_demo_order_intent():
    preflight = DemoOrderPreflight()
    intent = preflight.validate(OrderIntent(" eurusd ", " buy ", 0.01))

    assert intent == OrderIntent("EURUSD", "BUY", 0.01)


def test_blocks_non_demo_environment():
    with pytest.raises(DemoOrderPreflightError, match="environment=demo"):
        DemoOrderPreflight().validate(OrderIntent("EURUSD", "BUY", 0.01), environment="live")


def test_blocks_volume_above_controlled_limit():
    with pytest.raises(DemoOrderPreflightError, match="preflight limit"):
        DemoOrderPreflight().validate(OrderIntent("EURUSD", "BUY", 0.010001))


def test_blocks_invalid_side():
    with pytest.raises(DemoOrderPreflightError, match="side must be BUY or SELL"):
        DemoOrderPreflight().validate(OrderIntent("EURUSD", "HOLD", 0.01))


def test_blocks_limit_orders_until_pending_order_semantics_exist():
    with pytest.raises(DemoOrderPreflightError, match="pending-order semantics"):
        DemoOrderPreflight().validate(OrderIntent("EURUSD", "BUY", 0.01, limit_price=1.1))


def test_optional_symbol_allowlist_is_case_insensitive():
    preflight = DemoOrderPreflight(allowed_symbols=frozenset({"eurusd"}))
    intent = preflight.validate(OrderIntent("EURUSD", "SELL", 0.01))
    assert intent.symbol == "EURUSD"


def test_blocks_symbol_outside_allowlist():
    preflight = DemoOrderPreflight(allowed_symbols=frozenset({"EURUSD"}))
    with pytest.raises(DemoOrderPreflightError, match="not approved"):
        preflight.validate(OrderIntent("GBPUSD", "BUY", 0.01))


def test_validates_minimum_internal_state_shape():
    DemoOrderPreflight().validate_state(_state())


def test_blocks_incomplete_internal_state():
    with pytest.raises(DemoOrderPreflightError, match="missing required field: executions"):
        DemoOrderPreflight().validate_state({"cash": 1000.0, "positions": {}, "open_orders": []})
