import json
import tempfile
import unittest
from pathlib import Path

from scripts.agent_system_ci_gate import run_gate


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


class AgentSystemCIGateTests(unittest.TestCase):
    def test_run_gate_returns_ok_with_valid_runtime_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "AGENTS.md").write_text("# test\n", encoding="utf-8")
            (root / "docs" / "memory").mkdir(parents=True, exist_ok=True)
            (root / "docs" / "memory" / "self_improving_agent.md").write_text("# memory\n", encoding="utf-8")

            _write(
                root / "agent_system" / "config" / "required-agents.json",
                {
                    "required_agents": [
                        "orchestrator_agent",
                        "rag_agent",
                        "guardrails_agent",
                        "self_improving_agent",
                        "review_agent",
                    ]
                },
            )
            _write(
                root / "agent_system" / "config" / "architecture-contract.json",
                {
                    "required_outputs": [
                        "run_report",
                        "retrieval_trace",
                        "guardrail_report",
                        "closed_loop_verdict",
                    ],
                    "rag_sources": [
                        "AGENTS.md",
                        "docs/memory/self_improving_agent.md",
                        "agent_system/config/required-agents.json",
                    ],
                },
            )

            result = run_gate(root=root, run_id="ci-gate-unit", query="guardrails")
            self.assertTrue(result["ok"])
            self.assertEqual(result["report"]["status"], "done")
            self.assertEqual(result["report"]["closed_loop"]["status"], "pass")
            self.assertEqual(result["failures"], [])


if __name__ == "__main__":
    unittest.main()
