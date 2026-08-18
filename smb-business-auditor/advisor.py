from __future__ import annotations

import os
import pandas as pd


def mock_executive_summary(findings: pd.DataFrame, roadmap: pd.DataFrame) -> str:
    if findings.empty:
        return "No material gaps were detected by the current rule set. Review thresholds and data coverage before concluding the business is fully optimized."
    top = findings.head(3)
    themes = "; ".join(top["title"].tolist())
    now = roadmap[roadmap["phase"] == "0–90 days"]["initiative"].head(3).tolist()
    actions = "; ".join(now) if now else roadmap["initiative"].head(3).str.cat(sep="; ")
    return (
        f"The audit's highest-priority themes are: {themes}. "
        f"The first execution wave should focus on: {actions}. "
        "Each initiative has a KPI and measurement method so the roadmap can be updated based on observed impact rather than completion alone."
    )


def generate_executive_summary(findings: pd.DataFrame, roadmap: pd.DataFrame) -> tuple[str, str]:
    provider = os.getenv("LLM_PROVIDER", "mock").lower()
    if provider != "openai" or not os.getenv("OPENAI_API_KEY"):
        return mock_executive_summary(findings, roadmap), "mock"

    from openai import OpenAI

    client = OpenAI()
    model = os.getenv("OPENAI_MODEL", "gpt-5.6")
    finding_text = findings.head(8)[["area", "title", "evidence", "opportunity_score"]].to_dict("records")
    roadmap_text = roadmap.head(10)[["phase", "initiative", "primary_kpi", "measurement_method"]].to_dict("records")
    prompt = f"""You are an SMB operating advisor. Write a concise executive audit summary using only the structured findings below. Do not invent facts, benchmarks, dollar estimates, or causal claims. Separate observations from recommendations. Mention that measurement plans are proposed, not proof of impact.\n\nFindings:\n{finding_text}\n\nRoadmap:\n{roadmap_text}"""
    response = client.responses.create(model=model, input=prompt)
    return response.output_text, f"openai:{model}"
