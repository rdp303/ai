from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    llm_provider: str = os.getenv("LLM_PROVIDER", "mock").lower()
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-5")
    knowledge_backend: str = os.getenv("KNOWLEDGE_BACKEND", "local").lower()
    mcp_server_url: str = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8001/mcp")
    mcp_host: str = os.getenv("MCP_HOST", "127.0.0.1")
    mcp_port: int = int(os.getenv("MCP_PORT", "8001"))
    top_k: int = int(os.getenv("TOP_K", "4"))
    docs_dir: Path = Path(os.getenv("DOCS_DIR", str(ROOT / "docs")))
    log_db: Path = Path(os.getenv("LOG_DB", str(ROOT / "agent_logs.sqlite3")))


def get_settings() -> Settings:
    return Settings()
