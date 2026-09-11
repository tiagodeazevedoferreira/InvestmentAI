from __future__ import annotations

import argparse

import scripts.validate_mt5_demo as validator


def test_validate_mt5_demo_parser_accepts_decimal_volume(monkeypatch):
    monkeypatch.setenv("DOTO_MT5_SERVER", "DOTOGlobal-Real")
    monkeypatch.setenv("DOTO_MT5_LOGIN", "5344431")
    monkeypatch.setenv("DOTO_MT5_PASSWORD", "test-only")
    monkeypatch.setattr(
        validator,
        "MetaTrader5DemoGateway",
        lambda **kwargs: (_ for _ in ()).throw(validator.DemoBrokerError("stop after parsing")),
    )
    monkeypatch.setattr("sys.argv", ["validate_mt5_demo.py", "--check-order-symbol", "EURUSD", "--side", "BUY", "--quantity", "0.01"])

    try:
        validator.main()
    except validator.DemoBrokerError as exc:
        assert str(exc) == "stop after parsing"
    else:
        raise AssertionError("expected the gateway stub to stop execution after argument parsing")


def test_order_intent_quantity_is_float():
    intent = validator.OrderIntent(symbol="EURUSD", side="BUY", quantity=0.01)
    assert isinstance(intent.quantity, float)
    assert intent.quantity == 0.01
