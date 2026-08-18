from __future__ import annotations

from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

from audit_engine import run_audit
from roadmap import build_roadmap
from measurement import difference_in_differences, measurement_contracts, simulate_annual_impact
from advisor import generate_executive_summary

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

st.set_page_config(page_title="SMB Growth & Efficiency Auditor", layout="wide")
st.title("SMB Growth & Efficiency Auditor")
st.caption("Connect-like demo: QuickBooks-style financials + GA4 + paid media + website audit → gaps → roadmap → measurement plan.")

with st.sidebar:
    st.header("Demo controls")
    st.write("The included data intentionally contains several business problems so the audit has something to diagnose.")
    cvr_lift = st.slider("Scenario: website CVR lift", 0, 40, 15, 5) / 100
    paid_savings = st.slider("Scenario: paid-media savings", 0, 30, 10, 5) / 100
    margin_points = st.slider("Scenario: gross-margin improvement", 0.0, 5.0, 2.0, 0.5) / 100
    ar_days = st.slider("Scenario: A/R days reduced", 0, 25, 10, 1)

financials = pd.read_csv(DATA / "quickbooks_monthly.csv", parse_dates=["month"])
ga4 = pd.read_csv(DATA / "ga4_monthly.csv", parse_dates=["month"])
paid = pd.read_csv(DATA / "paid_media_monthly.csv", parse_dates=["month"])
website = pd.read_csv(DATA / "website_audit.csv")
geo = pd.read_csv(DATA / "geo_lift_example.csv")

findings = run_audit(financials, ga4, paid, website)
roadmap = build_roadmap(findings)
contracts = measurement_contracts(roadmap)
summary, provider = generate_executive_summary(findings, roadmap)

latest_12 = financials.tail(12)
revenue = latest_12["revenue"].sum()
gm = 1 - latest_12["cogs"].sum() / latest_12["revenue"].sum()
marketing_eff = latest_12["revenue"].sum() / latest_12["marketing_expense"].sum()
web_cvr = ga4.tail(12)["leads"].sum() / ga4.tail(12)["sessions"].sum()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Trailing 12-mo revenue", f"${revenue:,.0f}")
c2.metric("Gross margin", f"{gm:.1%}")
c3.metric("Revenue / marketing $", f"{marketing_eff:.2f}x")
c4.metric("Website lead CVR", f"{web_cvr:.2%}")

st.subheader("Executive summary")
st.write(summary)
st.caption(f"Narrative provider: {provider}. Metrics and findings are calculated in Python before any LLM narrative is generated.")

st.subheader("Audit findings")
show = findings[["severity", "area", "title", "evidence", "opportunity_score"]].copy()
st.dataframe(show, use_container_width=True, hide_index=True)

left, right = st.columns(2)
with left:
    st.subheader("Revenue & gross margin")
    fin_chart = financials.copy()
    fin_chart["gross_margin"] = 1 - fin_chart["cogs"] / fin_chart["revenue"]
    fig = px.line(fin_chart, x="month", y=["revenue"], markers=True)
    st.plotly_chart(fig, use_container_width=True)
    st.line_chart(fin_chart.set_index("month")["gross_margin"])
with right:
    st.subheader("Traffic vs leads")
    fig = px.line(ga4, x="month", y=["sessions", "leads"], markers=True)
    st.plotly_chart(fig, use_container_width=True)

st.subheader("6–12 month roadmap")
roadmap_display = roadmap[["phase", "initiative", "area", "problem", "primary_kpi", "baseline", "target", "measurement_method", "opportunity_score"]]
st.dataframe(roadmap_display, use_container_width=True, hide_index=True)

st.subheader("Measurement contracts")
st.dataframe(contracts, use_container_width=True, hide_index=True)

st.subheader("Impact simulator")
impact = simulate_annual_impact(financials, ga4, paid, cvr_lift, paid_savings, margin_points, ar_days)
i1, i2, i3, i4 = st.columns(4)
i1.metric("Directional profit impact", f"${impact['total_directional_profit_impact']:,.0f}")
i2.metric("Incremental revenue from CVR", f"${impact['incremental_revenue_from_cvr']:,.0f}")
i3.metric("Paid-media savings", f"${impact['annual_paid_media_savings']:,.0f}")
i4.metric("Working capital released", f"${impact['working_capital_released']:,.0f}")
st.caption("Scenario outputs are arithmetic planning estimates, not causal forecasts. Actual impact should be measured with the assigned experiment or quasi-experimental method.")

st.subheader("Incrementality example: Difference-in-Differences")
did = difference_in_differences(geo, outcome="signups")
st.write(
    f"Treated market change: {did['treated_change']:.1f} signups; control-market change: {did['control_change']:.1f}; "
    f"estimated incremental lift: **{did['incremental_lift']:.1f} signups per period**."
)
st.dataframe(geo, use_container_width=True, hide_index=True)

st.download_button("Download audit findings", findings.to_csv(index=False).encode(), "smb_audit_findings.csv", "text/csv")
st.download_button("Download roadmap", roadmap.to_csv(index=False).encode(), "smb_roadmap.csv", "text/csv")
