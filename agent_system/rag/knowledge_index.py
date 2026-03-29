from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Iterator


@dataclass
class RetrievalHit:
    namespace: str
    source_id: str
    content: str
    score: float
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "namespace": self.namespace,
            "source_id": self.source_id,
            "content": self.content,
            "score": round(self.score, 6),
            "metadata": self.metadata,
        }


class KnowledgeIndex:
    """Hybrid lexical retrieval index.

    The index keeps implementation local and dependency-light:
    - SQLite table as durable source
    - Optional FTS5 virtual table for ranking
    - Token overlap fallback when FTS is unavailable
    """

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._fts_enabled = True
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @contextmanager
    def _session(self) -> Iterator[sqlite3.Connection]:
        conn = self._connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _ensure_schema(self) -> None:
        with self._session() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    namespace TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    updated_at TEXT NOT NULL,
                    UNIQUE(namespace, source_id)
                )
                """
            )
            try:
                conn.execute(
                    """
                    CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts
                    USING fts5(content, namespace, source_id, content='documents', content_rowid='id')
                    """
                )
                conn.executescript(
                    """
                    CREATE TRIGGER IF NOT EXISTS documents_ai AFTER INSERT ON documents BEGIN
                      INSERT INTO documents_fts(rowid, content, namespace, source_id)
                      VALUES (new.id, new.content, new.namespace, new.source_id);
                    END;
                    CREATE TRIGGER IF NOT EXISTS documents_ad AFTER DELETE ON documents BEGIN
                      INSERT INTO documents_fts(documents_fts, rowid, content, namespace, source_id)
                      VALUES('delete', old.id, old.content, old.namespace, old.source_id);
                    END;
                    CREATE TRIGGER IF NOT EXISTS documents_au AFTER UPDATE ON documents BEGIN
                      INSERT INTO documents_fts(documents_fts, rowid, content, namespace, source_id)
                      VALUES('delete', old.id, old.content, old.namespace, old.source_id);
                      INSERT INTO documents_fts(rowid, content, namespace, source_id)
                      VALUES (new.id, new.content, new.namespace, new.source_id);
                    END;
                    """
                )
            except sqlite3.OperationalError:
                self._fts_enabled = False

    def upsert(
        self,
        namespace: str,
        source_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if not content.strip():
            return
        payload = json.dumps(metadata or {}, ensure_ascii=False)
        now = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
        with self._session() as conn:
            conn.execute(
                """
                INSERT INTO documents(namespace, source_id, content, metadata_json, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(namespace, source_id)
                DO UPDATE SET content=excluded.content, metadata_json=excluded.metadata_json, updated_at=excluded.updated_at
                """,
                (namespace, source_id, content, payload, now),
            )

    def bulk_upsert(self, items: Iterable[dict[str, Any]]) -> int:
        count = 0
        for item in items:
            self.upsert(
                namespace=str(item.get("namespace", "default")),
                source_id=str(item.get("source_id", f"item-{count}")),
                content=str(item.get("content", "")),
                metadata=dict(item.get("metadata", {})),
            )
            count += 1
        return count

    def query(self, query: str, top_k: int = 8, namespaces: list[str] | None = None) -> list[RetrievalHit]:
        q = query.strip()
        if not q:
            return []
        if self._fts_enabled:
            hits = self._query_fts(q, top_k, namespaces)
            if hits:
                return hits
        return self._query_fallback(q, top_k, namespaces)

    def _query_fts(self, query: str, top_k: int, namespaces: list[str] | None) -> list[RetrievalHit]:
        clauses: list[str] = []
        params: list[Any] = []
        if namespaces:
            placeholders = ",".join("?" for _ in namespaces)
            clauses.append(f"d.namespace IN ({placeholders})")
            params.extend(namespaces)
        where_sql = " AND ".join(clauses) if clauses else "1=1"
        sql = f"""
            SELECT d.namespace, d.source_id, d.content, d.metadata_json, d.updated_at,
                   bm25(documents_fts) AS rank
            FROM documents_fts
            JOIN documents d ON d.id = documents_fts.rowid
            WHERE documents_fts MATCH ? AND {where_sql}
            ORDER BY rank
            LIMIT ?
        """
        params = [query, *params, max(1, top_k)]
        with self._session() as conn:
            rows = conn.execute(sql, params).fetchall()
        results: list[RetrievalHit] = []
        for row in rows:
            # bm25 lower is better; convert to higher-is-better score.
            score = 1.0 / (1.0 + abs(float(row["rank"])))
            results.append(
                RetrievalHit(
                    namespace=row["namespace"],
                    source_id=row["source_id"],
                    content=row["content"],
                    score=score,
                    metadata=json.loads(row["metadata_json"]),
                )
            )
        return results

    def _query_fallback(self, query: str, top_k: int, namespaces: list[str] | None) -> list[RetrievalHit]:
        tokens = [item for item in query.lower().split() if item]
        if not tokens:
            return []
        clauses: list[str] = []
        params: list[Any] = []
        if namespaces:
            placeholders = ",".join("?" for _ in namespaces)
            clauses.append(f"namespace IN ({placeholders})")
            params.extend(namespaces)
        where_sql = " AND ".join(clauses) if clauses else "1=1"
        sql = f"""
            SELECT namespace, source_id, content, metadata_json, updated_at
            FROM documents
            WHERE {where_sql}
            ORDER BY updated_at DESC
            LIMIT 500
        """
        with self._session() as conn:
            rows = conn.execute(sql, params).fetchall()
        ranked: list[RetrievalHit] = []
        for row in rows:
            text = str(row["content"]).lower()
            overlap = sum(1 for token in tokens if token in text)
            if overlap == 0:
                continue
            ranked.append(
                RetrievalHit(
                    namespace=row["namespace"],
                    source_id=row["source_id"],
                    content=row["content"],
                    score=float(overlap),
                    metadata=json.loads(row["metadata_json"]),
                )
            )
        ranked.sort(key=lambda item: item.score, reverse=True)
        return ranked[: max(1, top_k)]
