from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)


def generate(seed: int = 42) -> None:
    rng = np.random.default_rng(seed)
    months = pd.date_range("2024-01-01", periods=30, freq="MS")
    t = np.arange(len(months))

    seasonal = 1 + 0.10 * np.sin(2 * np.pi * t / 12)
    revenue = (185_000 + 3_100 * t) * seasonal + rng.normal(0, 9_000, len(t))
    gross_margin = 0.46 - 0.0008 * t - np.where(t >= 20, 0.035, 0)
    cogs = revenue * (1 - gross_margin) + rng.normal(0, 2_500, len(t))
    operating_expense = 58_000 + 950 * t + rng.normal(0, 3_000, len(t))
    marketing_expense = 18_000 + 650 * t + np.where(t >= 18, 6_500, 0) + rng.normal(0, 1_200, len(t))
    customers = np.maximum(95, np.round(revenue / (1_650 + rng.normal(0, 80, len(t))))).astype(int)
    avg_invoice = revenue / customers
    ar_days = 31 + 0.55 * t + np.where(t >= 20, 7, 0) + rng.normal(0, 2, len(t))
    accounts_receivable = revenue / 30 * ar_days

    pd.DataFrame({
        "month": months,
        "revenue": revenue.round(2),
        "cogs": cogs.round(2),
        "operating_expense": operating_expense.round(2),
        "marketing_expense": marketing_expense.round(2),
        "accounts_receivable": accounts_receivable.round(2),
        "customers": customers,
        "average_invoice": avg_invoice.round(2),
    }).to_csv(DATA / "quickbooks_monthly.csv", index=False)

    sessions = 31_000 + 900 * t + rng.normal(0, 1_500, len(t))
    mobile_share = 0.62 + 0.002 * t
    mobile_sessions = sessions * mobile_share
    desktop_sessions = sessions - mobile_sessions
    base_cvr = 0.046 - 0.00015 * t - np.where(t >= 19, 0.006, 0)
    mobile_cvr = base_cvr * (0.78 - np.where(t >= 19, 0.07, 0))
    desktop_cvr = base_cvr * 1.18
    mobile_leads = rng.poisson(np.maximum(1, mobile_sessions * mobile_cvr))
    desktop_leads = rng.poisson(np.maximum(1, desktop_sessions * desktop_cvr))
    leads = mobile_leads + desktop_leads
    users = sessions * rng.uniform(0.78, 0.85, len(t))
    engaged_sessions = sessions * rng.uniform(0.54, 0.62, len(t))
    organic_sessions = sessions * rng.uniform(0.34, 0.41, len(t))
    paid_sessions = sessions * rng.uniform(0.28, 0.35, len(t))

    pd.DataFrame({
        "month": months,
        "sessions": sessions.round().astype(int),
        "users": users.round().astype(int),
        "engaged_sessions": engaged_sessions.round().astype(int),
        "leads": leads.astype(int),
        "mobile_sessions": mobile_sessions.round().astype(int),
        "mobile_leads": mobile_leads.astype(int),
        "desktop_sessions": desktop_sessions.round().astype(int),
        "desktop_leads": desktop_leads.astype(int),
        "organic_sessions": organic_sessions.round().astype(int),
        "paid_sessions": paid_sessions.round().astype(int),
    }).to_csv(DATA / "ga4_monthly.csv", index=False)

    rows = []
    channel_params = {
        "Google Ads": dict(base_spend=12_000, spend_trend=500, cpc=3.1, cpc_trend=0.045, lead_rate=0.080, close_rate=0.23),
        "Meta Ads": dict(base_spend=7_000, spend_trend=260, cpc=1.55, cpc_trend=0.012, lead_rate=0.045, close_rate=0.17),
        "YouTube": dict(base_spend=4_000, spend_trend=170, cpc=0.75, cpc_trend=0.008, lead_rate=0.018, close_rate=0.11),
    }
    for i, month in enumerate(months):
        for channel, p in channel_params.items():
            spend = p["base_spend"] + p["spend_trend"] * i + rng.normal(0, 700)
            if channel == "Google Ads" and i >= 19:
                spend += 5_000
            cpc = p["cpc"] + p["cpc_trend"] * i
            if channel == "Google Ads" and i >= 19:
                cpc += 0.9
            clicks = max(1, int(spend / cpc * rng.uniform(0.94, 1.06)))
            lead_rate = p["lead_rate"] * (0.92 if i >= 19 else 1.0)
            leads_ch = rng.binomial(clicks, min(0.3, lead_rate))
            customers_ch = rng.binomial(leads_ch, p["close_rate"])
            revenue_ch = customers_ch * rng.normal(1_700, 130)
            rows.append({"month": month, "channel": channel, "spend": round(spend, 2), "clicks": clicks, "leads": leads_ch, "customers": customers_ch, "attributed_revenue": round(max(0, revenue_ch), 2)})
    pd.DataFrame(rows).to_csv(DATA / "paid_media_monthly.csv", index=False)

    website = pd.DataFrame([
        ["/", "Homepage", 82_000, 4_450, 2_050, True, 200],
        ["/services", "Services", 48_500, 1_290, 3_150, True, 200],
        ["/pricing", "Pricing", 31_200, 620, 2_750, True, 200],
        ["/emergency-service", "Emergency Service", 29_900, 1_910, 2_250, True, 200],
        ["/blog/how-to-choose", "Blog: How to Choose", 26_800, 210, 4_350, False, 200],
        ["/locations/north", "North Location", 19_400, 410, 3_600, True, 200],
        ["/locations/south", "South Location", 17_900, 355, 3_900, True, 200],
        ["/contact", "Contact", 14_800, 2_050, 2_450, True, 200],
        ["/old-offer", "Old Promotion", 6_700, 25, 4_800, False, 200],
    ], columns=["url", "page_name", "sessions", "leads", "load_time_ms", "has_primary_cta", "status_code"])
    website["conversion_rate"] = website["leads"] / website["sessions"]
    website.to_csv(DATA / "website_audit.csv", index=False)

    periods = ["before"] * 6 + ["after"] * 6
    lift_rows = []
    for market, treated in [("North", 1), ("South", 0)]:
        for idx, period in enumerate(periods):
            baseline = 110 + idx * 1.5 + rng.normal(0, 4)
            treatment_lift = 18 if treated and period == "after" else 0
            natural_after = 5 if period == "after" else 0
            lift_rows.append({"market": market, "treated": treated, "period": period, "signups": round(baseline + treatment_lift + natural_after, 1)})
    pd.DataFrame(lift_rows).to_csv(DATA / "geo_lift_example.csv", index=False)


if __name__ == "__main__":
    generate()
    print(f"Demo data written to {DATA}")
