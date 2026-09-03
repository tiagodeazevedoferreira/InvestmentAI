import pytest

from app.services.automation_config import PaperAutomationConfig


def test_default_b3_universe_is_bounded():
    cfg = PaperAutomationConfig()
    assert cfg.symbols == ("PETR4", "VALE3", "ITUB4")
    assert cfg.provider_symbols == ("PETR4.SA", "VALE3.SA", "ITUB4.SA")
    assert cfg.enabled is False


def test_rejects_invalid_weight():
    with pytest.raises(ValueError):
        PaperAutomationConfig(target_weight=0)
