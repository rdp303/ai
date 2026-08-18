from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.llm import MockAnswerProvider  # noqa: E402
from app.retriever import KnowledgeRetriever  # noqa: E402


def main() -> int:
    cases = json.loads((ROOT / "evals" / "questions.json").read_text(encoding="utf-8"))
    retriever = KnowledgeRetriever(ROOT / "docs")
    answerer = MockAnswerProvider()

    retrieval_passes = 0
    citation_passes = 0
    permission_passes = 0
    permission_cases = 0

    print("Internal Knowledge Agent evals\n")

    for idx, case in enumerate(cases, start=1):
        results = retriever.search(case["question"], case["groups"], top_k=4)
        source_ids = [result.source_id for result in results]
        answer = answerer.answer(case["question"], results)

        expected = case.get("expected_source")
        forbidden = case.get("forbidden_source")

        retrieval_ok = expected is None or expected in source_ids
        citation_ok = expected is None or f"[{expected}]" in answer
        permission_ok = forbidden is None or forbidden not in source_ids

        if expected is not None:
            retrieval_passes += int(retrieval_ok)
            citation_passes += int(citation_ok)
        if forbidden is not None:
            permission_cases += 1
            permission_passes += int(permission_ok)

        status = "PASS" if retrieval_ok and citation_ok and permission_ok else "FAIL"
        print(f"{idx}. {status} — {case['question']}")
        print(f"   sources: {source_ids}")

    retrieval_total = sum(1 for case in cases if case.get("expected_source"))
    print("\nSummary")
    print(f"Retrieval hit@4: {retrieval_passes}/{retrieval_total}")
    print(f"Expected citation present: {citation_passes}/{retrieval_total}")
    print(f"Permission checks: {permission_passes}/{permission_cases}")

    success = (
        retrieval_passes == retrieval_total
        and citation_passes == retrieval_total
        and permission_passes == permission_cases
    )
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
