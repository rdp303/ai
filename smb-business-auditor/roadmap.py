from __future__ import annotations

import pandas as pd

PLAYBOOK = {
    "gross_margin": ("Run pricing + service-line margin review", "Review pricing, discounts, labor/material mix, and low-margin service lines; test targeted price increases.", "gross_margin", "time_series"),
    "marketing_efficiency": ("Reallocate marketing to profit-efficient demand", "Join channel spend to booked revenue/gross profit, cut obvious waste, and shift budget toward higher-quality demand.", "revenue_per_marketing_dollar", "interrupted_time_series"),
    "ar_days": ("Tighten invoicing and collections workflow", "Automate reminders, reduce invoice lag, and create an aging follow-up cadence.", "accounts_receivable_days", "before_after"),
    "website_conversion": ("Rebuild highest-traffic conversion paths", "Audit message-match, forms, CTAs, trust elements, and landing-page friction; prioritize controlled experiments.", "session_to_lead_rate", "ab_test"),
    "mobile_conversion_gap": ("Launch mobile conversion optimization sprint", "Simplify mobile forms, improve tap targets/speed, and test a mobile-first CTA flow.", "mobile_conversion_rate", "ab_test"),
    "paid_cac": ("Reset paid acquisition efficiency targets", "Review query/audience quality, bidding, landing pages, and offline conversion feedback; set CAC guardrails.", "paid_cac", "geo_or_holdout"),
    "revenue_growth": ("Diagnose growth by customer and service line", "Decompose growth into customer volume, average invoice, repeat rate, geography, and service mix before choosing growth investments.", "six_month_revenue_growth", "time_series"),
}


def _initiative_for(key: str) -> tuple[str, str, str, str]:
    if key.startswith("channel_cac::"):
        channel = key.split("::", 1)[1]
        return (
            f"Fix or resize {channel}",
            f"Audit targeting/query mix, conversion quality, and landing pages for {channel}; reduce spend until marginal economics improve.",
            "channel_cac",
            "geo_or_holdout",
        )
    if key.startswith("page_cvr::"):
        return ("Optimize an underperforming high-traffic page", "Run a focused CRO test on the flagged page: CTA, copy, proof, form friction, and offer alignment.", "page_conversion_rate", "ab_test")
    if key.startswith("page_speed::"):
        return ("Improve performance on a high-traffic page", "Reduce page weight, blocking scripts, and oversized assets; monitor speed and conversion together.", "page_load_time_ms", "before_after")
    return PLAYBOOK[key]


def build_roadmap(findings: pd.DataFrame) -> pd.DataFrame:
    if findings.empty:
        return pd.DataFrame()

    rows = []
    for _, finding in findings.iterrows():
        title, recommendation, kpi, method = _initiative_for(finding["key"])
        score = float(finding["opportunity_score"])
        effort = int(finding["effort"])
        if score >= 8 and effort <= 3:
            phase = "0–90 days"
        elif score >= 5:
            phase = "3–6 months"
        else:
            phase = "6–12 months"
        baseline = float(finding["baseline"])
        direction = finding["direction"]
        if direction == "higher_is_better":
            target = baseline * 1.12 if abs(baseline) < 10 else baseline * 1.08
        else:
            target = baseline * 0.88
        rows.append({
            "phase": phase,
            "initiative": title,
            "area": finding["area"],
            "problem": finding["title"],
            "evidence": finding["evidence"],
            "recommendation": recommendation,
            "primary_kpi": kpi,
            "baseline": baseline,
            "target": target,
            "measurement_method": method,
            "opportunity_score": score,
            "impact": int(finding["impact"]),
            "confidence": int(finding["confidence"]),
            "effort": effort,
        })
    phase_order = {"0–90 days": 0, "3–6 months": 1, "6–12 months": 2}
    out = pd.DataFrame(rows)
    out["phase_order"] = out["phase"].map(phase_order)
    return out.sort_values(["phase_order", "opportunity_score"], ascending=[True, False]).drop(columns="phase_order").reset_index(drop=True)
