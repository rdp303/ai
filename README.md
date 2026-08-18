# AI Agent Projects

A collection of practical AI-agent and LLM infrastructure projects built to explore how production agent systems retrieve context, use tools, enforce permissions, call models, expose APIs, log behavior, evaluate quality, and turn structured data into decisions.

## Projects

### 1. Internal Knowledge Agent

**Folder:** [`internal-knowledge-agent/`](internal-knowledge-agent/)

An employee-facing knowledge agent that answers policy and process questions using permission-aware retrieval, an optional MCP tool layer, LLM answer generation with sources, FastAPI, telemetry, and evals.

### 2. SMB Growth & Efficiency Auditor

**Folder:** [`smb-business-auditor/`](smb-business-auditor/)

An AI-assisted SMB audit that combines QuickBooks-style financials, GA4-style website metrics, paid-media data, and website audit data to:

- calculate financial, marketing, web, and operating KPIs
- identify gaps and efficiency issues with a deterministic audit engine
- prioritize opportunities using impact × confidence ÷ effort
- generate a 0–90 day, 3–6 month, and 6–12 month roadmap
- create a KPI + measurement contract for every initiative
- demonstrate before/after and Difference-in-Differences measurement
- simulate directional revenue, profit, marketing-savings, and working-capital impact
- optionally use an LLM to turn the already-calculated findings into an executive summary

The project includes fully synthetic data, so it can be run without QuickBooks, GA4, ad-platform, or LLM credentials.

## Repository philosophy

Each project is self-contained and runnable in demo mode. The goal is to separate the layers of an AI system — data/connectors, deterministic business logic, tools/retrieval, model reasoning, serving, observability, and evaluation — so each can be understood and improved independently.

Future folders can cover help-desk agents, finance/procurement document workflows, model routing, LLM observability, and agents with write-capable business-system tools.
