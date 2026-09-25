from __future__ import annotations

import pytest

from app.services.firebase_governance import inspect_firebase_usage, report_to_dict


class FakeFirebase:
    enabled = True

    def __init__(self, values):
        self.values = values

    def get(self, path):
        return self.values.get(path)


def test_usage_report_counts_records_and_bytes():
    report = inspect_firebase_usage(FakeFirebase({"paper/account": {"cash": 100}, "paper/ledger": {"a": {"x": 1}, "b": {"x": 2}}}), ["paper/account", "paper/ledger"], warning_bytes=50, critical_bytes=500)
    assert report.status == "ok"
    assert report.total_bytes > 0
    assert report.paths[1].records == 2
    assert report_to_dict(report)["paths"][0]["path"] == "paper/account"


def test_warning_and_critical_statuses_are_fail_closed():
    report = inspect_firebase_usage(FakeFirebase({"a": {"payload": "x" * 20}, "b": {"payload": "y" * 80}}), ["a", "b"], warning_bytes=40, critical_bytes=70)
    assert report.status == "critical"
    assert report.paths[0].status == "warning"
    assert report.paths[1].status == "critical"


@pytest.mark.parametrize("warning,critical", [(0, 10), (10, 0), (20, 10)])
def test_invalid_thresholds_fail_closed(warning, critical):
    with pytest.raises(ValueError):
        inspect_firebase_usage(FakeFirebase({"a": 1}), ["a"], warning_bytes=warning, critical_bytes=critical)


def test_unconfigured_firebase_fails_closed():
    class Disabled:
        enabled = False

    with pytest.raises(RuntimeError, match="not configured"):
        inspect_firebase_usage(Disabled(), ["paper/account"])
