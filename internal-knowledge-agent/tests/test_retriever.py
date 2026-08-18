from pathlib import Path

from app.retriever import KnowledgeRetriever

ROOT = Path(__file__).resolve().parents[1]


def test_retrieves_vendor_policy():
    retriever = KnowledgeRetriever(ROOT / "docs")
    results = retriever.search(
        "What approval is needed for a 20K vendor?",
        groups=["employees"],
        top_k=3,
    )
    assert results
    assert results[0].source_id == "procurement-vendor-approval"


def test_retrieves_parental_leave_policy():
    retriever = KnowledgeRetriever(ROOT / "docs")
    results = retriever.search(
        "How many weeks of parental leave do employees receive?",
        groups=["employees"],
        top_k=3,
    )
    assert results
    assert results[0].source_id == "hr-parental-leave"


def test_search_returns_unique_sources():
    retriever = KnowledgeRetriever(ROOT / "docs")
    results = retriever.search("contractor access provisioning", ["employees"], top_k=4)
    ids = [result.source_id for result in results]
    assert len(ids) == len(set(ids))
