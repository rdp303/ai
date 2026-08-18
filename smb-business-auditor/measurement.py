from __future__ import annotations

import numpy as np
import pandas as pd


def before_after(before: pd.Series, after: pd.Series) -> dict:
    b = float(before.mean())
    a = float(after.mean())
    delta = a - b
    pct = delta / b if b else np.nan
    return {"before": b, "after": a, "absolute_change": delta, "percent_change": pct}


def difference_in_differences(df: pd.DataFrame, outcome: str, treated_col: str = "treated", period_col: str = "period") -> dict:
    required = {outcome, treated_col, period_col}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    means = df.groupby([treated_col, period_col])[outcome].mean()
    try:
        treated_before = float(means.loc[(1, "before")])
        treated_after = float(means.loc[(1, "after")])
        control_before = float(means.loc[(0, "before")])
        control_after = float(means.loc[(0, "after")])
    except KeyError as exc:
        raise ValueError("Need treated/control observations in before and after periods") from exc

    treated_change = treated_after - treated_before
    control_change = control_after - control_before
    return {
        "treated_before": treated_before,
        "treated_after": treated_after,
        "control_before": control_before,
        "control_after": control_after,
        "treated_change": treated_change,
        "control_change": control_change,
        "incremental_lift": treated_change - control_change,
    }


def measurement_contracts(roadmap: pd.DataFrame) -> pd.DataFrame:
    if roadmap.empty:
        return pd.DataFrame()
    notes = {
        "ab_test": "Randomize eligible traffic when possible; compare conversion rates and report uncertainty.",
        "before_after": "Use for operational monitoring; treat as directional unless a credible counterfactual exists.",
        "time_series": "Track pre/post trend and seasonality; use interrupted time-series methods when enough history exists.",
        "interrupted_time_series": "Model the pre-intervention trajectory and test whether level/trend changes after launch.",
        "geo_or_holdout": "Use a matched geo/audience holdout when feasible; otherwise treat platform attribution as directional.",
    }
    out = roadmap[["initiative", "primary_kpi", "baseline", "target", "measurement_method", "phase"]].copy()
    out["measurement_note"] = out["measurement_method"].map(notes)
    return out


def simulate_annual_impact(financials: pd.DataFrame, ga4: pd.DataFrame, paid_media: pd.DataFrame, website_cvr_lift: float = 0.15, paid_spend_savings: float = 0.10, gross_margin_points: float = 0.02, ar_days_reduction: float = 10.0) -> dict:
    latest_12_fin = financials.sort_values("month").tail(12)
    latest_12_ga4 = ga4.sort_values("month").tail(12)
    dates = pd.to_datetime(paid_media["month"])
    last_date = dates.max()
    paid_12 = paid_media[dates >= last_date - pd.DateOffset(months=11)]

    annual_revenue = float(latest_12_fin["revenue"].sum())
    annual_customers = float(latest_12_fin["customers"].sum())
    revenue_per_customer = annual_revenue / annual_customers
    gm = 1 - latest_12_fin["cogs"].sum() / latest_12_fin["revenue"].sum()
    sessions = float(latest_12_ga4["sessions"].sum())
    leads = float(latest_12_ga4["leads"].sum())
    current_cvr = leads / sessions

    paid_customers = max(float(paid_12["customers"].sum()), 1.0)
    paid_leads = max(float(paid_12["leads"].sum()), 1.0)
    close_rate = min(1.0, paid_customers / paid_leads)

    incremental_leads = sessions * current_cvr * website_cvr_lift
    incremental_customers = incremental_leads * close_rate
    incremental_revenue = incremental_customers * revenue_per_customer
    incremental_gross_profit = incremental_revenue * gm

    annual_paid_spend = float(paid_12["spend"].sum())
    marketing_savings = annual_paid_spend * paid_spend_savings
    margin_profit = annual_revenue * gross_margin_points
    cash_released = annual_revenue / 365 * ar_days_reduction

    return {
        "incremental_leads": incremental_leads,
        "incremental_customers": incremental_customers,
        "incremental_revenue_from_cvr": incremental_revenue,
        "incremental_gross_profit_from_cvr": incremental_gross_profit,
        "annual_paid_media_savings": marketing_savings,
        "annual_gross_profit_from_margin": margin_profit,
        "working_capital_released": cash_released,
        "total_directional_profit_impact": incremental_gross_profit + marketing_savings + margin_profit,
    }
