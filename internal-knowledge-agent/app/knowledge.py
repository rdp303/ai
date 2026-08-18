from __future__ import annotations

from typing import Protocol

from .mcp_client import MCPKnowledgeClient
from .retriever import KnowledgeRetriever, SearchResult


class KnowledgeSource(Protocol):
    async def search(
        self,
        query: str,
        groups: list[str],
        top_k: int = 4,
    ) -> list[SearchResult]: ...


class LocalKnowledgeSource:
    def __init__(self, retriever: KnowledgeRetriever):
        self.retriever = retriever

    async def search(
        self,
        query: str,
        groups: list[str],
        top_k: int = 4,
    ) -> list[SearchResult]:
        return self.retriever.search(query=query, groups=groups, top_k=top_k)


class RemoteMCPKnowledgeSource:
    def __init__(self, server_url: str):
        self.client = MCPKnowledgeClient(server_url)

    async def search(
        self,
        query: str,
        groups: list[str],
        top_k: int = 4,
    ) -> list[SearchResult]:
        return await self.client.search(query=query, groups=groups, top_k=top_k)
