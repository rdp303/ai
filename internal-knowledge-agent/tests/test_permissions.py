from pathlib import Path

from app.retriever import KnowledgeRetriever

ROOT = Path(__file__).resolve().parents[1]


def test_employee_cannot_retrieve_restricted_snowflake_runbook():
    retriever = KnowledgeRetriever(ROOT / "docs")
    results = retriever.search(
        "Snowflake administrative access and production roles",
        groups=["employees"],
        top_k=5,
    )
    assert "it-snowflake-access" not in [result.source_id for result in results]


def test_it_group_can_retrieve_snowflake_runbook():
    retriever = KnowledgeRetriever(ROOT / "docs")
    results = retriever.search(
        "SSO works but my Snowflake role is missing",
        groups=["it"],
        top_k=3,
    )
    assert results
    assert results[0].source_id == "it-snowflake-access"
