# SMB Growth & Efficiency Auditor

A simulated AI-assisted business audit for small and midsize businesses. It combines **QuickBooks-style financial data, GA4-style website data, paid-media performance, and a lightweight website audit** to identify gaps, prioritize opportunities, create a 6–12 month roadmap, and define how each initiative should be measured.

The project is deliberately runnable with **dummy data and no credentials**.

## Business question

> Where is this business losing growth, margin, cash flow, or marketing efficiency — what should it do next, and how will we know whether the recommendation worked?

## Workflow

```text
QuickBooks-style financials ─┐
GA4-style web data ──────────┤
Paid-media data ─────────────┼─→ KPI layer → audit rules → prioritized findings
Website crawl/audit ─────────┘                         ↓
                                               6–12 month roadmap
                                                       ↓
                                               measurement contract
                                                       ↓
                                        experiment / lift measurement
```

An optional LLM layer turns the structured findings into an executive summary. The **metrics, thresholds, evidence, prioritization, and impact arithmetic are calculated in Python first** so the model is not asked to invent business facts.

## Included demo data

The repo includes synthetic QuickBooks-style financials, GA4-style web metrics, paid-media performance, page-level website audit data, and a small treated/control geo dataset. The generator intentionally creates problems such as margin compression, rising paid CAC, worsening website conversion, a mobile conversion gap, slower A/R collection, and underperforming high-traffic pages.

## What the auditor does

The deterministic audit engine currently flags examples such as slowing revenue growth, gross-margin compression, falling revenue per marketing dollar, increasing A/R days, declining session-to-lead conversion, mobile conversion gaps, rising paid CAC, inefficient channels, and weak or slow high-traffic pages.

Each finding receives an **impact × confidence ÷ effort** opportunity score.

## Roadmap

Every finding is converted into an initiative and placed into one of three execution windows:

```text
0–90 days
3–6 months
6–12 months
```

Each initiative includes evidence, recommendation, primary KPI, baseline, target, measurement method, and impact/confidence/effort scores.

## Measurement layer

The project deliberately distinguishes **observed improvement** from **incremental/causal lift**. Supported demo measurement patterns include before/after monitoring, A/B tests, interrupted time series, geo/audience holdouts, and Difference-in-Differences.

The Streamlit app includes a synthetic geo example that estimates incremental signup lift using Difference-in-Differences.

## Impact simulator

The sidebar lets a user simulate assumptions such as +15% website conversion-rate lift, 10% paid-media savings, +2 percentage points of gross margin, and 10 fewer A/R days. The app translates those assumptions into directional estimates for incremental customers/revenue, gross profit, marketing savings, and working capital released.

These outputs are **planning arithmetic, not causal forecasts**. The roadmap's measurement contract is how actual impact should be evaluated.

## Run it

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

No API key is required. The app defaults to a deterministic mock executive summary.

### Optional LLM narrative

```bash
export LLM_PROVIDER=openai
export OPENAI_API_KEY='...'
export OPENAI_MODEL='gpt-5.6'
streamlit run app.py
```

The LLM receives the already-calculated findings and roadmap and is instructed not to invent facts or causal claims.

## Rebuild the dummy data

```bash
python generate_demo_data.py
```

## Tests

```bash
pytest -q
```

## Project structure

```text
smb-business-auditor/
├── README.md
├── app.py
├── audit_engine.py
├── roadmap.py
├── measurement.py
├── advisor.py
├── generate_demo_data.py
├── requirements.txt
├── .env.example
├── data/
│   ├── quickbooks_monthly.csv
│   ├── ga4_monthly.csv
│   ├── paid_media_monthly.csv
│   ├── website_audit.csv
│   └── geo_lift_example.csv
└── tests/
    ├── test_audit_engine.py
    └── test_measurement.py
```

## Natural production extensions

The demo uses CSVs so the logic is easy to inspect. A production version could replace those files with authenticated connectors for QuickBooks, GA4/Search Console, Google Ads/Meta, a CRM, call tracking, and a website crawler. The same normalized KPI and measurement layers could remain behind those connectors.
