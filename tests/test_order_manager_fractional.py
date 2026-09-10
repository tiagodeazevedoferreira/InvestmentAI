from backend.app.services.order_manager import OrderIntent, SimulatedBroker


def test_order_intent_supports_fractional_quantity():
    result = SimulatedBroker().submit(OrderIntent("EURUSD", "BUY", 0.01))
    assert result["quantity"] == 0.01
