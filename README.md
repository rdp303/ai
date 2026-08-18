# AI Agent Projects

A collection of practical AI-agent and LLM infrastructure projects built to explore how production agent systems retrieve context, use tools, enforce permissions, call models, expose APIs, log behavior, and evaluate quality.

## Projects

### 1. Internal Knowledge Agent

**Folder:** [`internal-knowledge-agent/`](internal-knowledge-agent/)

An employee-facing knowledge agent that answers questions such as:

- What is our parental leave policy?
- What approval is required for a $20K vendor?
- What is the process for provisioning a contractor?

The project demonstrates a production-shaped agent architecture:

```text
User question
    ↓
FastAPI service
    ↓
permission-aware knowledge retrieval
    ↓
MCP tool layer (optional remote backend)
    ↓
LLM answer generation
    ↓
answer + source citations
    ↓
SQLite logs + evaluation harness
```

It includes a local no-API-key mode for learning and tests, plus an OpenAI Responses API provider for real model generation.

## Repository philosophy

Each project is self-contained. Future folders can cover help-desk agents, finance/procurement document workflows, model routing, LLM observability, and agents with write-capable business-system tools.
