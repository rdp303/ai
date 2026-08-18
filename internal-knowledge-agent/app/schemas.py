from __future__ import annotations

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    user_id: str = Field(default="anonymous", min_length=1, max_length=200)
    groups: list[str] = Field(default_factory=lambda: ["employees"])
    top_k: int | None = Field(default=None, ge=1, le=10)


class Source(BaseModel):
    source_id: str
    title: str
    score: float
    excerpt: str


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]
    provider: str
    latency_ms: float


class HealthResponse(BaseModel):
    status: str
    llm_provider: str
    knowledge_backend: str
