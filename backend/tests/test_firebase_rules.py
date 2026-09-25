import json
from pathlib import Path


def test_realtime_database_rules_are_default_deny():
    path = Path(__file__).parents[2] / "firebase" / "database.rules.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    rules = data["rules"]

    assert rules[".read"] is False
    assert rules[".write"] is False
    assert "public" not in rules
    assert "signals" not in rules
    assert "predictions" not in rules
