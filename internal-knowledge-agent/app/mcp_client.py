from __future__ import annotations

import json
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from .retriever import SearchResult


class MCPKnowledgeClient:
    """Thin client for the knowledge-search MCP server."""

    def __init__(self, server_url: str):
        self.server_url = server_url

    async def search(
        self,
        query: str,
        groups: list[str],
        top_k: int = 4,
    ) -> list[SearchResult]:
        async with streamable_http_client(self.server_url) as (
            read_stream,
            write_stream,
            _,
        ):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(
                    "search_internal_docs",
                    {
                        "query": query,
                        "groups": groups,
                        "top_k": top_k,
                    },
                )

        payload: Any = getattr(result, "structuredContent", None)
        if payload is None:
            payload = getattr(result, "structured_content", None)

        # MCP servers may wrap a typed return value in a `result` key.
        if isinstance(payload, dict) and "result" in payload:
            payload = payload["result"]

        if payload is None:
            text_parts = [
                item.text
                for item in getattr(result, "content", [])
                if hasattr(item, "text")
            ]
            if text_parts:
                try:
                    payload = json.loads(text_parts[0])
                except json.JSONDecodeError:
                    payload = []

        if not isinstance(payload, list):
            return []

        return [
            SearchResult(
                source_id=str(item["source_id"]),
                title=str(item["title"]),
                score=float(item["score"]),
                excerpt=str(item["excerpt"]),
            )
            for item in payload
            if isinstance(item, dict)
            and {"source_id", "title", "score", "excerpt"}.issubset(item)
        ]
