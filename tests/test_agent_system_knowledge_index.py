import tempfile
import unittest
from pathlib import Path

from agent_system.rag.knowledge_index import KnowledgeIndex


class KnowledgeIndexTests(unittest.TestCase):
    def test_upsert_and_query_returns_hit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "rag.sqlite"
            index = KnowledgeIndex(db)
            index.upsert(
                namespace="workspace",
                source_id="doc-1",
                content="harness recovery and guardrails policy",
                metadata={"kind": "doc"},
            )
            hits = index.query("guardrails harness", top_k=3)
            self.assertGreaterEqual(len(hits), 1)
            self.assertEqual(hits[0].source_id, "doc-1")


if __name__ == "__main__":
    unittest.main()
