import json
import tempfile
import unittest
from pathlib import Path

from agent_system.runtime import run_pipeline


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


class RuntimePipelineTests(unittest.TestCase):
    def test_preview_pipeline_generates_harness_artifacts(self) -> None:
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
            _write(
                root / "agent_system" / "input" / "agent-results.sample.json",
                {
                    "agent_results": [
                        {"agent": "orchestrator_agent", "status": "done", "payload": {}, "missing_data": []},
                        {"agent": "rag_agent", "status": "done", "payload": {}, "missing_data": []},
                        {"agent": "guardrails_agent", "status": "done", "payload": {}, "missing_data": []},
                        {"agent": "self_improving_agent", "status": "done", "payload": {}, "missing_data": []},
                        {"agent": "review_agent", "status": "needs_confirmation", "payload": {}, "missing_data": []},
                    ]
                },
            )

            report = run_pipeline(
                root=root,
                run_id="unit-run",
                query="guardrails",
                mode="preview",
            )
            self.assertEqual(report["status"], "needs_confirmation")
            self.assertTrue((root / "docs" / "harness" / "architecture_guardrails.json").exists())
            self.assertTrue((root / "docs" / "harness" / "closed_loop_verdict.json").exists())


if __name__ == "__main__":
    unittest.main()
