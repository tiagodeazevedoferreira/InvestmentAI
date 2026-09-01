import unittest
from datetime import datetime, timezone

from backend.app.services.doto import DotoSignalAdapter
from backend.app.services.external_intelligence import Direction, ExternalSignal, RiskGate, SignalFusion
from backend.app.services.paper_broker import PaperBroker


class ExternalIntelligenceTests(unittest.TestCase):
    def test_doto_normalization(self):
        signal = DotoSignalAdapter().normalize({"direction": "BUY", "confidence": 78, "entry": 100}, "AAPL")
        self.assertEqual(signal.direction, Direction.LONG)
        self.assertAlmostEqual(signal.confidence or 0, .78)
        self.assertEqual(signal.source, "doto_ai")

    def test_conflicting_sources_are_blocked(self):
        now = datetime.now(timezone.utc)
        fused = SignalFusion().fuse([
            ExternalSignal("AAPL", now, Direction.LONG, .8, source="internal_ml"),
            ExternalSignal("AAPL", now, Direction.SHORT, .8, source="doto_ai"),
        ])
        allowed, reasons = RiskGate().evaluate(fused, environment="paper")
        self.assertFalse(allowed)
        self.assertTrue(reasons)

    def test_single_provider_is_not_enough(self):
        now = datetime.now(timezone.utc)
        fused = SignalFusion().fuse([ExternalSignal("AAPL", now, Direction.LONG, .95, source="doto_ai")])
        allowed, reasons = RiskGate().evaluate(fused, environment="paper")
        self.assertFalse(allowed)
        self.assertIn("independent evidence threshold not met", reasons)

    def test_paper_broker_never_uses_live(self):
        broker = PaperBroker(cash=1000)
        order = broker.submit("AAPL", "BUY", 2, 100)
        self.assertEqual(order["environment"], "paper")
        self.assertEqual(broker.snapshot()["positions"]["AAPL"], 2)


if __name__ == "__main__":
    unittest.main()
