from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_doto_mt5_controlled_demo.py"


def test_controlled_demo_preflight_script_is_fail_closed():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "execution_enabled=False" in source
    assert "order_send: NOT CALLED" in source
    assert "DEMO execution is disabled" in source
    assert "--volume" in source
    assert "DEFAULT_VOLUME = 0.01" in source


def test_controlled_demo_preflight_targets_confirmed_demo_identity():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "DEFAULT_LOGIN = 5344431" in source
    assert 'DEFAULT_SERVER = "DOTOGlobal-Real"' in source
    assert "DEFAULT_TERMINAL" in source
