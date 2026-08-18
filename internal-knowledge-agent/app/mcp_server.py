from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from .config import get_settings
from .retriever import KnowledgeRetriever

settings = get_settings()
retriever = KnowledgeRetriever(settings.docs_dir)

mcp = FastMCP(
    "Internal Knowledge",
    host=settings.mcp_host,
    port=settings.mcp_port,
    stateless_http=True,
    json_response=True,
)


@mcp.tool()
def search_internal_docs(
    query: str,
    groups: list[str],
    top_k: int = 4,
) -> list[dict[str, object]]:
    """Search authorized internal documentation for an employee question.

    Args:
        query: Natural-language question or search query.
        groups: Trusted authorization groups for the caller.
        top_k: Maximum number of source documents to return.
    """
    top_k = max(1, min(int(top_k), 10))
    return [
        result.to_dict()
        for result in retriever.search(query=query, groups=groups, top_k=top_k)
    ]


@mcp.tool()
def list_accessible_sources(groups: list[str]) -> list[dict[str, str]]:
    """List source IDs/titles visible to the supplied authorization groups."""
    normalized = {group.strip().lower() for group in groups if group.strip()}
    seen: set[str] = set()
    sources: list[dict[str, str]] = []

    for chunk in retriever.chunks:
        if chunk.source_id in seen:
            continue
        if "all" not in chunk.allowed_groups and not chunk.allowed_groups.intersection(normalized):
            continue
        seen.add(chunk.source_id)
        sources.append({"source_id": chunk.source_id, "title": chunk.title})

    return sources


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
