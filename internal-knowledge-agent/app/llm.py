from __future__ import annotations

from typing import Protocol

from openai import OpenAI

from .retriever import SearchResult


class AnswerProvider(Protocol):
    name: str

    def answer(self, question: str, sources: list[SearchResult]) -> str: ...


def _context_block(sources: list[SearchResult]) -> str:
    return "\n\n".join(
        f"[{source.source_id}] {source.title}\n{source.excerpt}"
        for source in sources
    )


class MockAnswerProvider:
    """No-key answerer used for demos, tests, and retrieval debugging."""

    name = "mock"

    def answer(self, question: str, sources: list[SearchResult]) -> str:
        if not sources:
            return (
                "I couldn't find an authorized internal source that answers that question. "
                "Try rephrasing it or contact the appropriate internal team."
            )

        primary = sources[0]
        supporting = " ".join(f"[{source.source_id}]" for source in sources[:3])
        return (
            f"Based on {primary.title}: {primary.excerpt} "
            f"Sources: {supporting}"
        )


class OpenAIAnswerProvider:
    name = "openai"

    def __init__(self, model: str):
        self.model = model
        self.client = OpenAI()

    def answer(self, question: str, sources: list[SearchResult]) -> str:
        if not sources:
            return (
                "I couldn't find an authorized internal source that answers that question. "
                "I won't guess without supporting internal documentation."
            )

        context = _context_block(sources)
        response = self.client.responses.create(
            model=self.model,
            instructions=(
                "You are an internal company knowledge assistant. Answer only from the "
                "provided internal context. Do not invent policy details. If the context is "
                "insufficient, say so. Cite factual claims using the exact source IDs in square "
                "brackets, for example [hr-parental-leave]. Keep the answer concise and useful."
            ),
            input=(
                f"Employee question:\n{question}\n\n"
                f"Authorized internal context:\n{context}"
            ),
        )
        return response.output_text.strip()


def build_answer_provider(provider: str, openai_model: str) -> AnswerProvider:
    if provider == "mock":
        return MockAnswerProvider()
    if provider == "openai":
        return OpenAIAnswerProvider(openai_model)
    raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")
