from types import SimpleNamespace

import pytest

from app.services.mt5_market_data import MT5MarketDataError, MetaTrader5MarketDataGateway


class FakeMT5:
    def __init__(self):
        self.shutdown_called = False

    def initialize(self, **kwargs):
        self.initialize_kwargs = kwargs
        return True

    def shutdown(self):
        self.shutdown_called = True

    def last_error(self):
        return (-1, "error")

    def account_info(self):
        return SimpleNamespace(login=5344431, server="DOTOGlobal-Real")

    def terminal_info(self):
        return SimpleNamespace(connected=True)

    def symbol_select(self, symbol, enable):
        self.selected = (symbol, enable)
        return True

    def symbol_info(self, symbol):
        return SimpleNamespace(digits=5, point=0.00001, trade_mode=0)

    def symbol_info_tick(self, symbol):
        return SimpleNamespace(
            bid=1.16289,
            ask=1.16304,
            last=0.0,
            time=1788990543,
            time_msc=1788990543784,
        )


def gateway(fake):
    return MetaTrader5MarketDataGateway(
        terminal_path="C:/DOTO/terminal64.exe",
        expected_login=5344431,
        expected_server="DOTOGlobal-Real",
        mt5_module=fake,
    )


def test_connect_and_read_eurusd_quote():
    fake = FakeMT5()
    g = gateway(fake)

    g.connect()
    quote = g.quote(" eurusd ")

    assert quote.symbol == "EURUSD"
    assert quote.bid == pytest.approx(1.16289)
    assert quote.ask == pytest.approx(1.16304)
    assert quote.spread == pytest.approx(0.00015)
    assert quote.time_msc == 1788990543784
    assert fake.selected == ("EURUSD", True)

    g.close()
    assert fake.shutdown_called is True


def test_symbol_info_is_read_only():
    fake = FakeMT5()
    g = gateway(fake)
    g.connect()

    info = g.symbol_info("EURUSD")

    assert info.symbol == "EURUSD"
    assert info.digits == 5
    assert info.point == pytest.approx(0.00001)


def test_quote_requires_connection():
    g = gateway(FakeMT5())

    with pytest.raises(MT5MarketDataError, match="not connected"):
        g.quote("EURUSD")


def test_rejects_unexpected_account():
    fake = FakeMT5()
    fake.account_info = lambda: SimpleNamespace(login=123, server="DOTOGlobal-Real")
    g = gateway(fake)

    with pytest.raises(MT5MarketDataError, match="Unexpected MT5 account"):
        g.connect()


def test_rejects_unexpected_server():
    fake = FakeMT5()
    fake.account_info = lambda: SimpleNamespace(login=5344431, server="MetaQuotes-Demo")
    g = gateway(fake)

    with pytest.raises(MT5MarketDataError, match="Unexpected MT5 server"):
        g.connect()


def test_rejects_empty_symbol():
    fake = FakeMT5()
    g = gateway(fake)
    g.connect()

    with pytest.raises(ValueError, match="Symbol is required"):
        g.quote("  ")
