import pandas as pd

from backend.app.services.data_quality import validate_market_data


def frame():
    return pd.DataFrame(
        {
            "open": [10.0, 11.0, 12.0],
            "high": [11.0, 12.0, 13.0],
            "low": [9.0, 10.0, 11.0],
            "close": [10.5, 11.5, 12.5],
            "volume": [100, 200, 300],
        },
        index=pd.to_datetime(["2026-01-02", "2026-01-05", "2026-01-06"], utc=True),
    )


def test_clean_daily_data_passes_and_reports_coverage():
    report = validate_market_data("VALE3", frame())
    assert report.valid
    assert report.rows == 3
    assert report.start.startswith("2026-01-02")
    assert report.end.startswith("2026-01-06")
    assert report.large_calendar_gaps == 0


def test_invalid_ohlc_fails_gate():
    df = frame()
    df.loc[df.index[1], "high"] = 10.0
    report = validate_market_data("VALE3", df)
    assert not report.valid
    assert report.invalid_ohlc_rows == 1


def test_negative_volume_fails_gate():
    df = frame()
    df.loc[df.index[1], "volume"] = -1
    report = validate_market_data("VALE3", df)
    assert not report.valid
    assert report.negative_volume_rows == 1


def test_missing_column_fails_gate():
    df = frame().drop(columns=["volume"])
    report = validate_market_data("VALE3", df)
    assert not report.valid
    assert report.missing_columns == ("volume",)


def test_duplicate_timestamp_fails_gate():
    df = pd.concat([frame(), frame().iloc[[0]]])
    report = validate_market_data("VALE3", df)
    assert not report.valid
    assert report.duplicate_timestamps == 1
