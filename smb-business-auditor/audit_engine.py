from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable
import pandas as pd
import numpy as np


@dataclass(frozen=True)
class Finding:
    key: str
    area: str
    title: str
    severity: str
    evidence: str
    primary_kpi: str
    baseline: float
    comparison: float
    direction: str
    impact: int
    confidence: int
    effort: int

    @property
    def opportunity_score(self) -> float:
        return round((self.impact * self.confidence) / max(self.effort, 1), 2)

    def to_dict(self) -> dict:
        row = asdict(self)
        row["opportunity_score"] = self.opportunity_score
        return row


def _periods(df: pd.DataFrame, months: int = 6) -> tuple[pd.DataFrame, pd.DataFrame]:
    ordered = df.sort_values("month").copy()
    if len(ordered) < months * 2:
        raise ValueError(f"Need at least {months * 2} monthly observations")
    return ordered.iloc[-months:], ordered.iloc[-months * 2:-months]


def _pct_change(current: float, prior: float) -> float:
    if prior == 0:
        return np.nan
    return current / prior - 1


def audit_financials(financials: pd.DataFrame) -> list[Finding]:
    current, prior = _periods(financials)
    findings: list[Finding] = []

    cur_rev = current["revenue"].sum()
    pri_rev = prior["revenue"].sum()
    growth = _pct_change(cur_rev, pri_rev)
    if growth < 0.06:
        findings.append(Finding(
            "revenue_growth", "Financial", "Revenue growth has slowed", "medium",
            f"Latest 6-month revenue changed {growth:.1%} versus the prior 6 months.",
            "six_month_revenue_growth", growth, 0.06, "higher_is_better", 4, 4, 3,
        ))

    cur_gm = 1 - current["cogs"].sum() / current["revenue"].sum()
    pri_gm = 1 - prior["cogs"].sum() / prior["revenue"].sum()
    gm_change = cur_gm - pri_gm
    if gm_change < -0.015:
        findings.append(Finding(
            "gross_margin", "Financial", "Gross margin is compressing", "high",
            f"Gross margin fell from {pri_gm:.1%} to {cur_gm:.1%} ({gm_change:+.1%} pts).",
            "gross_margin", cur_gm, pri_gm, "higher_is_better", 5, 5, 3,
        ))

    cur_marketing_eff = cur_rev / current["marketing_expense"].sum()
    pri_marketing_eff = pri_rev / prior["marketing_expense"].sum()
    eff_change = _pct_change(cur_marketing_eff, pri_marketing_eff)
    if eff_change < -0.10:
        findings.append(Finding(
            "marketing_efficiency", "Marketing", "Revenue per marketing dollar is declining", "high",
            f"Revenue / marketing spend fell from {pri_marketing_eff:.2f}x to {cur_marketing_eff:.2f}x ({eff_change:.1%}).",
            "revenue_per_marketing_dollar", cur_marketing_eff, pri_marketing_eff, "higher_is_better", 5, 5, 2,
        ))

    cur_ar_days = (current["accounts_receivable"].sum() / current["revenue"].sum()) * 30
    pri_ar_days = (prior["accounts_receivable"].sum() / prior["revenue"].sum()) * 30
    if cur_ar_days > 45 and cur_ar_days > pri_ar_days + 3:
        findings.append(Finding(
            "ar_days", "Operations", "Cash collection is slowing", "medium",
            f"Approximate A/R days increased from {pri_ar_days:.1f} to {cur_ar_days:.1f} days.",
            "accounts_receivable_days", cur_ar_days, pri_ar_days, "lower_is_better", 4, 4, 2,
        ))

    return findings


def audit_ga4(ga4: pd.DataFrame) -> list[Finding]:
    current, prior = _periods(ga4)
    findings: list[Finding] = []

    cur_cvr = current["leads"].sum() / current["sessions"].sum()
    pri_cvr = prior["leads"].sum() / prior["sessions"].sum()
    cvr_change = _pct_change(cur_cvr, pri_cvr)
    if cvr_change < -0.08:
        findings.append(Finding(
            "website_conversion", "Website", "Website lead conversion rate is falling", "high",
            f"Session-to-lead rate fell from {pri_cvr:.2%} to {cur_cvr:.2%} ({cvr_change:.1%}).",
            "session_to_lead_rate", cur_cvr, pri_cvr, "higher_is_better", 5, 5, 2,
        ))

    mobile_cvr = current["mobile_leads"].sum() / current["mobile_sessions"].sum()
    desktop_cvr = current["desktop_leads"].sum() / current["desktop_sessions"].sum()
    gap = mobile_cvr / desktop_cvr if desktop_cvr else np.nan
    if gap < 0.75:
        findings.append(Finding(
            "mobile_conversion_gap", "Website", "Mobile visitors convert materially worse than desktop", "high",
            f"Mobile CVR is {mobile_cvr:.2%} versus {desktop_cvr:.2%} on desktop ({gap:.0%} of desktop).",
            "mobile_conversion_rate", mobile_cvr, desktop_cvr, "higher_is_better", 5, 5, 2,
        ))

    return findings


def audit_paid_media(paid_media: pd.DataFrame) -> list[Finding]:
    ordered = paid_media.copy()
    ordered["month"] = pd.to_datetime(ordered["month"])
    cutoff = ordered["month"].drop_duplicates().sort_values().iloc[-6]
    prior_cutoff = ordered["month"].drop_duplicates().sort_values().iloc[-12]
    current = ordered[ordered["month"] >= cutoff]
    prior = ordered[(ordered["month"] >= prior_cutoff) & (ordered["month"] < cutoff)]
    findings: list[Finding] = []

    def cac(frame: pd.DataFrame) -> float:
        customers = frame["customers"].sum()
        return frame["spend"].sum() / customers if customers else np.inf

    cur_cac = cac(current)
    pri_cac = cac(prior)
    change = _pct_change(cur_cac, pri_cac)
    if change > 0.08:
        findings.append(Finding(
            "paid_cac", "Marketing", "Paid acquisition cost is rising", "high",
            f"Blended paid CAC rose from ${pri_cac:,.0f} to ${cur_cac:,.0f} ({change:.1%}).",
            "paid_cac", cur_cac, pri_cac, "lower_is_better", 5, 5, 3,
        ))

    for channel, frame in current.groupby("channel"):
        channel_cac = cac(frame)
        if np.isfinite(channel_cac) and channel_cac > cur_cac * 1.25 and frame["spend"].sum() > 15_000:
            findings.append(Finding(
                f"channel_cac::{channel}", "Marketing", f"{channel} is inefficient versus the paid-media average", "medium",
                f"{channel} CAC is ${channel_cac:,.0f} versus blended paid CAC of ${cur_cac:,.0f}.",
                "channel_cac", channel_cac, cur_cac, "lower_is_better", 4, 4, 2,
            ))
    return findings


def audit_website_pages(website: pd.DataFrame) -> list[Finding]:
    findings: list[Finding] = []
    median_cvr = website["conversion_rate"].median()
    high_traffic = website["sessions"] >= website["sessions"].median()
    weak = website[high_traffic & (website["conversion_rate"] < median_cvr * 0.65)]
    for _, row in weak.iterrows():
        findings.append(Finding(
            f"page_cvr::{row['url']}", "Website", f"High-traffic page underperforms: {row['page_name']}", "medium",
            f"{row['sessions']:,.0f} sessions with {row['conversion_rate']:.2%} CVR versus site median {median_cvr:.2%}.",
            "page_conversion_rate", float(row["conversion_rate"]), float(median_cvr), "higher_is_better", 4, 4, 2,
        ))

    slow = website[(website["load_time_ms"] > 3500) & (website["sessions"] >= website["sessions"].median())]
    for _, row in slow.iterrows():
        findings.append(Finding(
            f"page_speed::{row['url']}", "Website", f"Slow high-traffic page: {row['page_name']}", "medium",
            f"Median-like traffic with {row['load_time_ms']:,.0f} ms load time.",
            "page_load_time_ms", float(row["load_time_ms"]), 3000.0, "lower_is_better", 3, 4, 2,
        ))
    return findings


def run_audit(financials: pd.DataFrame, ga4: pd.DataFrame, paid_media: pd.DataFrame, website: pd.DataFrame) -> pd.DataFrame:
    financials = financials.copy(); financials["month"] = pd.to_datetime(financials["month"])
    ga4 = ga4.copy(); ga4["month"] = pd.to_datetime(ga4["month"])
    findings: Iterable[Finding] = (
        audit_financials(financials)
        + audit_ga4(ga4)
        + audit_paid_media(paid_media)
        + audit_website_pages(website)
    )
    frame = pd.DataFrame([f.to_dict() for f in findings])
    if frame.empty:
        return frame
    severity_rank = {"high": 0, "medium": 1, "low": 2}
    frame["severity_rank"] = frame["severity"].map(severity_rank)
    return frame.sort_values(["severity_rank", "opportunity_score"], ascending=[True, False]).drop(columns="severity_rank").reset_index(drop=True)
