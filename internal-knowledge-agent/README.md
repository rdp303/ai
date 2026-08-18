# Internal Knowledge Agent

A production-shaped learning project for building an employee-facing AI knowledge agent.

The agent answers internal questions such as:

> What is our parental leave policy?
>
> What approval is required for a $20K vendor?
>
> What is the process for provisioning a contractor?

It retrieves only documents the caller is allowed to access, sends the relevant context to an LLM, and returns an answer with source IDs. The same retrieval layer is also exposed as an MCP tool so it can be used by other agent hosts.

## Architecture

```text
                         ┌─────────────────────────┐
                         │   Internal Markdown     │
                         │   policies / runbooks   │
                         └────────────┬────────────┘
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │ Permission-aware RAG    │
                         │ TF-IDF + cosine search  │
                         └────────────┬────────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    │                                   │
                    ▼                                   ▼
        ┌──────────────────────┐            ┌──────────────────────┐
        │ FastAPI agent API    │            │ MCP tool server      │
        │ POST /ask            │            │ search_internal_docs │
        └──────────┬───────────┘            └──────────────────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │ Answer provider      │
        │ mock or OpenAI       │
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │ Answer + sources     │
        │ SQLite interaction   │
        │ logging              │
        └──────────────────────┘
```

## What this project teaches

- RAG: chunking, retrieval, scoring, and source grounding
- permission-aware retrieval before context reaches the model
- MCP tools as a standardized interface to internal knowledge
- FastAPI service design for an agent backend
- provider abstraction so model vendors can be swapped
- structured logging for latency, provider, user, and retrieved sources
- lightweight evals for retrieval quality and grounded answers
- safe fallback behavior when the answer is not in the knowledge base

## Quick start: no API key

```bash
cd internal-knowledge-agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.api:api --reload
```

Then ask a question:

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H 'Content-Type: application/json' \
  -d '{
    "question": "What approval is required for a $20K vendor?",
    "user_id": "demo-user",
    "groups": ["employees"]
  }'
```

By default `LLM_PROVIDER=mock`, so the project runs without credentials.

## Use OpenAI

Set environment variables:

```bash
export LLM_PROVIDER=openai
export OPENAI_API_KEY='...'
export OPENAI_MODEL='gpt-5'
uvicorn app.api:api --reload
```

The OpenAI provider uses the Responses API and instructs the model to answer only from retrieved context and to cite source IDs.

## Run the MCP server

```bash
python -m app.mcp_server
```

The Streamable HTTP MCP endpoint is:

```text
http://127.0.0.1:8001/mcp
```

It exposes:

```text
search_internal_docs
```

You can inspect the server with the MCP Inspector or connect to it from another MCP-capable host/client.

## Use MCP as the agent's knowledge backend

Run the MCP server in one terminal:

```bash
python -m app.mcp_server
```

Then run the API with:

```bash
export KNOWLEDGE_BACKEND=mcp
export MCP_SERVER_URL=http://127.0.0.1:8001/mcp
uvicorn app.api:api --reload
```

The API now retrieves context through MCP instead of calling the local retriever directly.

## Permission model

Each Markdown document has front matter:

```yaml
---
id: procurement-vendor-approval
title: Vendor Approval Policy
allowed_groups: employees,finance,procurement
---
```

A document is eligible for retrieval only when:

- `allowed_groups` contains `all`, or
- the caller belongs to at least one allowed group.

Permission filtering happens **before retrieved text is returned to the agent**.

## Add internal documents

Drop Markdown files into:

```text
docs/
```

Use this format:

```markdown
---
id: unique-document-id
title: Human-readable title
allowed_groups: employees,hr
---

# Policy

Policy content here...
```

Restart the service after changing the demo knowledge base.

## API

### `POST /ask`

Request:

```json
{
  "question": "What is our parental leave policy?",
  "user_id": "employee-123",
  "groups": ["employees"],
  "top_k": 4
}
```

Response:

```json
{
  "answer": "...",
  "sources": [
    {
      "source_id": "hr-parental-leave",
      "title": "Parental Leave Policy",
      "score": 0.71
    }
  ],
  "provider": "mock",
  "latency_ms": 14.2
}
```

Other routes:

```text
GET /health
GET /logs?limit=25
```

## Evals

Run the lightweight evaluation set:

```bash
python scripts/run_evals.py
```

The eval harness checks:

- whether the expected source appears in the retrieved top-K results
- whether permission-restricted documents remain inaccessible
- whether the answer includes the expected source ID

This is intentionally small and transparent so it is easy to extend with more realistic company questions later.

## Tests

```bash
pytest -q
```

## Project structure

```text
internal-knowledge-agent/
├── README.md
├── requirements.txt
├── .env.example
├── app/
│   ├── __init__.py
│   ├── api.py
│   ├── agent.py
│   ├── config.py
│   ├── knowledge.py
│   ├── llm.py
│   ├── logging_store.py
│   ├── mcp_client.py
│   ├── mcp_server.py
│   ├── retriever.py
│   └── schemas.py
├── docs/
│   ├── parental_leave.md
│   ├── vendor_approval.md
│   ├── contractor_provisioning.md
│   └── snowflake_access.md
├── evals/
│   └── questions.json
├── scripts/
│   └── run_evals.py
└── tests/
    ├── test_agent.py
    ├── test_permissions.py
    └── test_retriever.py
```

## Security note

This demo uses caller-supplied groups to make the permission boundary visible. A real deployment should derive identity and authorization claims from trusted SSO/OAuth middleware rather than accepting group membership from request JSON.

Do not treat RAG as an authorization system by itself. Authorization should be enforced before protected content is returned to the model or user.
