from pathlib import Path
import pandas as pd

from measurement import before_after, difference_in_differences, simulate_annual_impact

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def test_before_after():
    result = before_after(pd.Series([10, 12]), pd.Series([15, 17]))
    assert result["before"] == 11
    assert result["after"] == 16
    assert result["absolute_change"] == 5


def test_difference_in_differences_positive_lift():
    geo = pd.read_csv(DATA / "geo_lift_example.csv")
    result = difference_in_differences(geo, "signups")
    assert result["incremental_lift"] > 10


def test_simulator_returns_positive_directional_values():
    financials = pd.read_csv(DATA / "quickbooks_monthly.csv")
    ga4 = pd.read_csv(DATA / "ga4_monthly.csv")
    paid = pd.read_csv(DATA / "paid_media_monthly.csv")
    result = simulate_annual_impact(financials, ga4, paid)
    assert result["incremental_revenue_from_cvr"] > 0
    assert result["annual_paid_media_savings"] > 0
    assert result["working_capital_released"] > 0
