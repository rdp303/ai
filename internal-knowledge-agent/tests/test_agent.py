import asyncio
from pathlib import Path

from app.agent import InternalKnowledgeAgent
from app.knowledge import LocalKnowledgeSource
from app.llm import MockAnswerProvider
from app.logging_store import InteractionLogStore
from app.retriever import KnowledgeRetriever
from app.schemas import AskRequest

ROOT = Path(__file__).resolve().parents[1]


def test_agent_returns_sources_and_logs_metadata(tmp_path):
    agent = InternalKnowledgeAgent(
        knowledge=LocalKnowledgeSource(KnowledgeRetriever(ROOT / "docs")),
        answer_provider=MockAnswerProvider(),
        log_store=InteractionLogStore(tmp_path / "logs.sqlite3"),
        knowledge_backend_name="local",
        default_top_k=4,
    )

    response = asyncio.run(
        agent.ask(
            AskRequest(
                question="What is the process for provisioning a contractor?",
                user_id="test-user",
                groups=["employees"],
            )
        )
    )

    assert response.sources
    assert response.sources[0].source_id == "it-contractor-provisioning"
    assert "[it-contractor-provisioning]" in response.answer

    logs = agent.log_store.recent(1)
    assert len(logs) == 1
    assert logs[0]["source_ids"][0] == "it-contractor-provisioning"
    assert logs[0]["user_hash"] != "test-user"


def test_agent_refuses_to_guess_without_authorized_source(tmp_path):
    agent = InternalKnowledgeAgent(
        knowledge=LocalKnowledgeSource(KnowledgeRetriever(ROOT / "docs")),
        answer_provider=MockAnswerProvider(),
        log_store=InteractionLogStore(tmp_path / "logs.sqlite3"),
        knowledge_backend_name="local",
    )

    response = asyncio.run(
        agent.ask(
            AskRequest(
                question="What is the secret Snowflake admin escalation procedure?",
                user_id="employee",
                groups=["employees"],
            )
        )
    )

    assert all(source.source_id != "it-snowflake-access" for source in response.sources)
