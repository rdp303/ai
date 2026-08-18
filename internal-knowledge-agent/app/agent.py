from __future__ import annotations

from time import perf_counter

from .knowledge import KnowledgeSource
from .llm import AnswerProvider
from .logging_store import InteractionLogStore
from .schemas import AskRequest, AskResponse, Source


class InternalKnowledgeAgent:
    def __init__(
        self,
        *,
        knowledge: KnowledgeSource,
        answer_provider: AnswerProvider,
        log_store: InteractionLogStore,
        knowledge_backend_name: str,
        default_top_k: int = 4,
    ):
        self.knowledge = knowledge
        self.answer_provider = answer_provider
        self.log_store = log_store
        self.knowledge_backend_name = knowledge_backend_name
        self.default_top_k = default_top_k

    async def ask(self, request: AskRequest) -> AskResponse:
        started = perf_counter()
        top_k = request.top_k or self.default_top_k

        results = await self.knowledge.search(
            query=request.question,
            groups=request.groups,
            top_k=top_k,
        )
        answer = self.answer_provider.answer(request.question, results)
        latency_ms = (perf_counter() - started) * 1000

        sources = [
            Source(
                source_id=result.source_id,
                title=result.title,
                score=float(result.score),
                excerpt=result.excerpt,
            )
            for result in results
        ]

        self.log_store.write(
            user_id=request.user_id,
            groups=request.groups,
            question=request.question,
            source_ids=[source.source_id for source in sources],
            provider=self.answer_provider.name,
            knowledge_backend=self.knowledge_backend_name,
            latency_ms=latency_ms,
        )

        return AskResponse(
            answer=answer,
            sources=sources,
            provider=self.answer_provider.name,
            latency_ms=round(latency_ms, 2),
        )
