from pathlib import Path
import pandas as pd

from audit_engine import run_audit
from roadmap import build_roadmap

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def load():
    return (
        pd.read_csv(DATA / "quickbooks_monthly.csv"),
        pd.read_csv(DATA / "ga4_monthly.csv"),
        pd.read_csv(DATA / "paid_media_monthly.csv"),
        pd.read_csv(DATA / "website_audit.csv"),
    )


def test_demo_data_produces_material_findings():
    findings = run_audit(*load())
    keys = set(findings["key"])
    assert "gross_margin" in keys
    assert "website_conversion" in keys
    assert "mobile_conversion_gap" in keys
    assert "paid_cac" in keys


def test_findings_are_prioritized():
    findings = run_audit(*load())
    assert findings.iloc[0]["severity"] == "high"
    assert findings["opportunity_score"].gt(0).all()


def test_roadmap_has_measurement_for_each_finding():
    findings = run_audit(*load())
    roadmap = build_roadmap(findings)
    assert len(roadmap) == len(findings)
    assert roadmap["measurement_method"].notna().all()
    assert set(roadmap["phase"]).issubset({"0–90 days", "3–6 months", "6–12 months"})
