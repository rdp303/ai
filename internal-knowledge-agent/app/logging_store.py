from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class InteractionLogStore:
    """Privacy-conscious operational telemetry for agent requests."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    user_hash TEXT NOT NULL,
                    group_count INTEGER NOT NULL,
                    question_length INTEGER NOT NULL,
                    source_ids_json TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    knowledge_backend TEXT NOT NULL,
                    latency_ms REAL NOT NULL,
                    source_count INTEGER NOT NULL
                )
                """
            )

    @staticmethod
    def _hash_user(user_id: str) -> str:
        return hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:16]

    def write(
        self,
        *,
        user_id: str,
        groups: list[str],
        question: str,
        source_ids: list[str],
        provider: str,
        knowledge_backend: str,
        latency_ms: float,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO interactions (
                    created_at, user_hash, group_count, question_length,
                    source_ids_json, provider, knowledge_backend,
                    latency_ms, source_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now(timezone.utc).isoformat(),
                    self._hash_user(user_id),
                    len(groups),
                    len(question),
                    json.dumps(source_ids),
                    provider,
                    knowledge_backend,
                    float(latency_ms),
                    len(source_ids),
                ),
            )

    def recent(self, limit: int = 25) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 200))
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, created_at, user_hash, group_count, question_length,
                       source_ids_json, provider, knowledge_backend,
                       latency_ms, source_count
                FROM interactions
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            {
                "id": row["id"],
                "created_at": row["created_at"],
                "user_hash": row["user_hash"],
                "group_count": row["group_count"],
                "question_length": row["question_length"],
                "source_ids": json.loads(row["source_ids_json"]),
                "provider": row["provider"],
                "knowledge_backend": row["knowledge_backend"],
                "latency_ms": row["latency_ms"],
                "source_count": row["source_count"],
            }
            for row in rows
        ]
