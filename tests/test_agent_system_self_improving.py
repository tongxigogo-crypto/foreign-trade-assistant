import tempfile
import unittest
from pathlib import Path

from agent_system.learning.self_improving import LearningRecord, SelfImprovingLedger, utc_now


class SelfImprovingTests(unittest.TestCase):
    def test_record_writes_incident_and_memory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger = SelfImprovingLedger(
                memory_file=root / "memory.md",
                incidents_file=root / "incidents.json",
            )
            ledger.record(
                LearningRecord(
                    timestamp=utc_now(),
                    category="checkpoint",
                    status="active",
                    context="unit-test",
                    signal="signal",
                    rule="rule",
                    action="action",
                    scope="test",
                )
            )
            incidents = ledger.load_incidents()
            self.assertEqual(len(incidents), 1)
            self.assertIn("checkpoint", (root / "memory.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
