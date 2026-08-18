from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass(frozen=True)
class DocumentChunk:
    source_id: str
    title: str
    allowed_groups: frozenset[str]
    text: str
    chunk_index: int


@dataclass(frozen=True)
class SearchResult:
    source_id: str
    title: str
    score: float
    excerpt: str

    def to_dict(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "title": self.title,
            "score": round(float(self.score), 6),
            "excerpt": self.excerpt,
        }


def _parse_front_matter(text: str, fallback_id: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---"):
        return {
            "id": fallback_id,
            "title": fallback_id.replace("-", " ").title(),
            "allowed_groups": "all",
        }, text

    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"Malformed front matter in {fallback_id}")

    metadata: dict[str, str] = {}
    for raw_line in parts[1].strip().splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        key, sep, value = raw_line.partition(":")
        if sep:
            metadata[key.strip()] = value.strip().strip('"').strip("'")

    metadata.setdefault("id", fallback_id)
    metadata.setdefault("title", metadata["id"].replace("-", " ").title())
    metadata.setdefault("allowed_groups", "all")
    return metadata, parts[2].strip()


def _chunk_markdown(body: str, max_chars: int = 1100) -> list[str]:
    """Create readable chunks while preserving headings with their following text."""
    blocks = [block.strip() for block in re.split(r"\n\s*\n", body) if block.strip()]
    if not blocks:
        return []

    chunks: list[str] = []
    current = ""
    active_heading = ""

    for block in blocks:
        if block.startswith("#"):
            active_heading = block

        candidate = block if not current else f"{current}\n\n{block}"
        if len(candidate) <= max_chars:
            current = candidate
            continue

        if current:
            chunks.append(current)

        if active_heading and not block.startswith("#"):
            current = f"{active_heading}\n\n{block}"
        else:
            current = block

        while len(current) > max_chars:
            split_at = current.rfind(" ", 0, max_chars)
            if split_at < max_chars // 2:
                split_at = max_chars
            chunks.append(current[:split_at].strip())
            current = current[split_at:].strip()
            if active_heading and current and not current.startswith("#"):
                current = f"{active_heading}\n\n{current}"

    if current:
        chunks.append(current)

    return chunks


def _excerpt(text: str, limit: int = 420) -> str:
    flat = re.sub(r"\s+", " ", text).strip()
    if len(flat) <= limit:
        return flat
    return flat[: limit - 1].rstrip() + "…"


class KnowledgeRetriever:
    """Small permission-aware lexical retriever for internal Markdown docs."""

    def __init__(self, docs_dir: Path):
        self.docs_dir = Path(docs_dir)
        self.chunks = self._load_chunks()
        if not self.chunks:
            raise ValueError(f"No Markdown knowledge documents found in {self.docs_dir}")

        corpus = [f"{chunk.title}. {chunk.text}" for chunk in self.chunks]
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
            sublinear_tf=True,
        )
        self.matrix = self.vectorizer.fit_transform(corpus)

    def _load_chunks(self) -> list[DocumentChunk]:
        chunks: list[DocumentChunk] = []
        for path in sorted(self.docs_dir.glob("*.md")):
            metadata, body = _parse_front_matter(
                path.read_text(encoding="utf-8"),
                fallback_id=path.stem.replace("_", "-"),
            )
            groups = frozenset(
                group.strip().lower()
                for group in metadata["allowed_groups"].split(",")
                if group.strip()
            ) or frozenset({"all"})

            for idx, text in enumerate(_chunk_markdown(body)):
                chunks.append(
                    DocumentChunk(
                        source_id=metadata["id"],
                        title=metadata["title"],
                        allowed_groups=groups,
                        text=text,
                        chunk_index=idx,
                    )
                )
        return chunks

    @staticmethod
    def _authorized(chunk: DocumentChunk, groups: set[str]) -> bool:
        if "all" in chunk.allowed_groups:
            return True
        return bool(chunk.allowed_groups.intersection(groups))

    def search(
        self,
        query: str,
        groups: list[str] | set[str] | tuple[str, ...],
        top_k: int = 4,
        min_score: float = 0.01,
    ) -> list[SearchResult]:
        query = query.strip()
        if not query:
            return []

        normalized_groups = {str(group).strip().lower() for group in groups if str(group).strip()}
        query_vector = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vector, self.matrix).ravel()

        ranked = np.argsort(scores)[::-1]
        results: list[SearchResult] = []
        seen_sources: set[str] = set()

        for idx in ranked:
            score = float(scores[idx])
            if score < min_score:
                break

            chunk = self.chunks[int(idx)]
            if not self._authorized(chunk, normalized_groups):
                continue

            # Keep the best-matching chunk from each source so citations stay concise.
            if chunk.source_id in seen_sources:
                continue

            results.append(
                SearchResult(
                    source_id=chunk.source_id,
                    title=chunk.title,
                    score=score,
                    excerpt=_excerpt(chunk.text),
                )
            )
            seen_sources.add(chunk.source_id)

            if len(results) >= top_k:
                break

        return results
