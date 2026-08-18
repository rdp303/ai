from __future__ import annotations

from fastapi import FastAPI, Query

from .agent import InternalKnowledgeAgent
from .config import get_settings
from .knowledge import LocalKnowledgeSource, RemoteMCPKnowledgeSource
from .llm import build_answer_provider
from .logging_store import InteractionLogStore
from .retriever import KnowledgeRetriever
from .schemas import AskRequest, AskResponse, HealthResponse

settings = get_settings()


def build_agent() -> InternalKnowledgeAgent:
    if settings.knowledge_backend == "local":
        knowledge = LocalKnowledgeSource(KnowledgeRetriever(settings.docs_dir))
    elif settings.knowledge_backend == "mcp":
        knowledge = RemoteMCPKnowledgeSource(settings.mcp_server_url)
    else:
        raise ValueError(
            f"Unsupported KNOWLEDGE_BACKEND: {settings.knowledge_backend}. Use local or mcp."
        )

    answer_provider = build_answer_provider(
        provider=settings.llm_provider,
        openai_model=settings.openai_model,
    )
    log_store = InteractionLogStore(settings.log_db)

    return InternalKnowledgeAgent(
        knowledge=knowledge,
        answer_provider=answer_provider,
        log_store=log_store,
        knowledge_backend_name=settings.knowledge_backend,
        default_top_k=settings.top_k,
    )


agent = build_agent()
api = FastAPI(
    title="Internal Knowledge Agent",
    version="0.1.0",
    description="Permission-aware internal knowledge retrieval and grounded answer generation.",
)


@api.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        llm_provider=settings.llm_provider,
        knowledge_backend=settings.knowledge_backend,
    )


@api.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest) -> AskResponse:
    return await agent.ask(request)


@api.get("/logs")
def logs(limit: int = Query(default=25, ge=1, le=200)) -> list[dict]:
    return agent.log_store.recent(limit)
