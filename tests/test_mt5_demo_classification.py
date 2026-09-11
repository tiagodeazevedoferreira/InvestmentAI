from types import SimpleNamespace

import pytest

from app.services.mt5_demo import DemoBrokerError, MetaTrader5DemoGateway, MT5DemoBroker


class FakeMT5:
    ACCOUNT_TRADE_MODE_DEMO = 0
    ACCOUNT_TRADE_MODE_CONTEST = 1
    ACCOUNT_TRADE_MODE_REAL = 2

    def __init__(self, account):
        self.account = account
        self.initialized = False
        self.shutdown_called = False

    def initialize(self, **kwargs):
        self.initialized = True
        return True

    def account_info(self):
        return self.account

    def shutdown(self):
        self.shutdown_called = True


def account(*, login="5344431", server="DOTOGlobal-Real", company="DOTO Global Ltd", trade_mode=0):
    return SimpleNamespace(
        login=login,
        server=server,
        company=company,
        trade_mode=trade_mode,
        balance=52000.0,
        equity=52000.0,
        currency="BRL",
        trade_allowed=True,
    )


def gateway(fake_mt5, *, demo_logins=None):
    gateway = MetaTrader5DemoGateway(demo_account_logins=demo_logins or set())
    gateway._mt5 = fake_mt5
    return gateway


def test_doto_demo_login_is_allowed_on_real_named_server():
    fake = FakeMT5(account(trade_mode=FakeMT5.ACCOUNT_TRADE_MODE_REAL))
    broker = MT5DemoBroker(gateway(fake, demo_logins={"5344431"}))

    assert broker.initialize() is True
    snapshot = broker.account()

    assert snapshot.login == "5344431"
    assert snapshot.server == "DOTOGlobal-Real"
    assert snapshot.trade_allowed is True


def test_real_named_doto_server_is_rejected_without_explicit_demo_allowlist():
    fake = FakeMT5(account(trade_mode=FakeMT5.ACCOUNT_TRADE_MODE_REAL))
    broker = MT5DemoBroker(gateway(fake))

    with pytest.raises(DemoBrokerError, match="non-demo"):
        broker.initialize()

    assert fake.shutdown_called is True


def test_regular_demo_server_does_not_need_allowlist():
    fake = FakeMT5(account(server="DOTOGlobal-Demo", trade_mode=FakeMT5.ACCOUNT_TRADE_MODE_DEMO))
    broker = MT5DemoBroker(gateway(fake))

    assert broker.initialize() is True


def test_allowlisted_login_must_still_be_a_doto_account():
    fake = FakeMT5(account(company="Other Broker", server="OtherBroker-Real", trade_mode=FakeMT5.ACCOUNT_TRADE_MODE_REAL))
    broker = MT5DemoBroker(gateway(fake, demo_logins={"5344431"}))

    with pytest.raises(DemoBrokerError, match="non-demo"):
        broker.initialize()


def test_doto_demo_allowlist_is_required_again_during_account_validation():
    fake = FakeMT5(account(trade_mode=FakeMT5.ACCOUNT_TRADE_MODE_REAL))
    gateway_instance = gateway(fake, demo_logins={"5344431"})
    broker = MT5DemoBroker(gateway_instance)

    broker.initialize()
    assert broker.account().login == "5344431"

    gateway_instance.demo_account_logins = frozenset()
    with pytest.raises(DemoBrokerError, match="non-demo"):
        broker.account()
