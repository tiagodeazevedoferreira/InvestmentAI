import pytest

from app.services.fundamentals import derived_multiples, invested_capital, roic


def test_invested_capital_uses_explicit_definition():
    assert invested_capital(100.0, 50.0, 20.0) == 130.0


def test_roic_uses_nopat_over_invested_capital():
    # NOPAT = 20 * (1 - 25%) = 15; invested capital = 100 + 50 - 20 = 130.
    assert roic(20.0, 0.25, 100.0, 50.0, 20.0) == pytest.approx(15 / 130)


def test_roic_returns_none_when_required_data_is_missing():
    assert roic(None, 0.25, 100.0, 50.0, 20.0) is None
    assert roic(20.0, None, 100.0, 50.0, 20.0) is None
    assert roic(20.0, 0.25, None, 50.0, 20.0) is None


@pytest.mark.parametrize("tax_rate", [-0.01, 1.01])
def test_roic_rejects_invalid_tax_rate(tax_rate):
    with pytest.raises(ValueError, match="tax rate"):
        roic(20.0, tax_rate, 100.0, 50.0, 20.0)


def test_roic_rejects_non_positive_invested_capital():
    with pytest.raises(ValueError, match="invested capital"):
        roic(20.0, 0.25, 10.0, 5.0, 20.0)


def test_derived_multiples_exposes_roic_without_changing_existing_inputs():
    result = derived_multiples(
        10.0, 10.0, 100.0, 12.0, 200.0, 30.0, 140.0, 2.0,
        operating_income=20.0,
        tax_rate=0.25,
        total_debt=50.0,
        cash=20.0,
    )
    assert result["roic"] == pytest.approx(15 / 130)
