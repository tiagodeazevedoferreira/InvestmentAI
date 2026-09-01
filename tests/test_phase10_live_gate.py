import unittest
from backend.app.services.live_authorization import LiveAuthorizationGate


class Phase10LiveGateTests(unittest.TestCase):
    def setUp(self):
        self.gate = LiveAuthorizationGate()
        self.base = dict(
            trading_mode="live",
            live_trading_enabled=True,
            model_approved=True,
            risk_gate_enabled=True,
            shadow_validation_passed=True,
            kill_switch=False,
            reconciliation_healthy=True,
            broker_demo_validated=True,
            max_position_notional=1000,
            proposed_notional=100,
            signal_confidence=.90,
        )

    def test_all_conditions_are_required(self):
        result = self.gate.evaluate(**self.base)
        self.assertTrue(result.authorized)

    def test_defaults_fail_closed(self):
        result = self.gate.evaluate(**{**self.base, "live_trading_enabled": False})
        self.assertFalse(result.authorized)

    def test_kill_switch_blocks(self):
        result = self.gate.evaluate(**{**self.base, "kill_switch": True})
        self.assertFalse(result.authorized)
        self.assertIn("kill switch is active", result.reasons)

    def test_unhealthy_reconciliation_blocks(self):
        result = self.gate.evaluate(**{**self.base, "reconciliation_healthy": False})
        self.assertFalse(result.authorized)

    def test_demo_validation_is_required(self):
        result = self.gate.evaluate(**{**self.base, "broker_demo_validated": False})
        self.assertFalse(result.authorized)

    def test_position_limit_blocks(self):
        result = self.gate.evaluate(**{**self.base, "proposed_notional": 1001})
        self.assertFalse(result.authorized)

    def test_confidence_blocks(self):
        result = self.gate.evaluate(**{**self.base, "signal_confidence": .74})
        self.assertFalse(result.authorized)


if __name__ == "__main__":
    unittest.main()
