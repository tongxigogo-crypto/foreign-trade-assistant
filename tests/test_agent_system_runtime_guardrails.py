import json
import tempfile
import unittest
from pathlib import Path

from agent_system.runtime import run_pipeline


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


class RuntimeGuardrailsTests(unittest.TestCase):
    def _prepare_root(self, root: Path) -> None:
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
                "review_mode": {
                    "code_edit_forbidden_paths": ["外贸助理_交接包"],
                    "software_edit_default": False,
                },
            },
        )
        _write(
            root / "agent_system" / "config" / "runtime-policy.json",
            {
                "active_task": "runtime-policy-test-task",
                "current_goal": "runtime-policy-test-goal",
                "next_actions": ["x", "y"],
                "summary": "runtime-policy-test-summary",
            },
        )

    def test_runtime_uses_runtime_policy_in_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._prepare_root(root)
            run_pipeline(root=root, run_id="policy-check", query="guardrails", mode="confirm_write")

            session = json.loads((root / "docs" / "harness" / "session_state.json").read_text(encoding="utf-8"))
            self.assertEqual(session["active_task"], "runtime-policy-test-task")
            self.assertEqual(session["current_goal"], "runtime-policy-test-goal")
            self.assertEqual(session["next_actions"], ["x", "y"])
            self.assertTrue(session["last_git_status"])

    def test_required_outputs_and_review_mode_checks_present_and_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._prepare_root(root)
            report = run_pipeline(root=root, run_id="output-check", query="guardrails", mode="confirm_write")

            checks = {item["name"]: bool(item["passed"]) for item in report["closed_loop"]["checks"]}
            self.assertTrue(checks.get("output_exists:run_report"))
            self.assertTrue(checks.get("output_exists:retrieval_trace"))
            self.assertTrue(checks.get("output_exists:guardrail_report"))
            self.assertTrue(checks.get("output_exists:closed_loop_verdict"))
            self.assertTrue(checks.get("review_mode_forbidden_paths_enforced"))
            self.assertEqual(report["status"], "done")
            self.assertEqual(report["closed_loop"]["status"], "pass")

    def test_quick_audit_adds_incremental_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._prepare_root(root)
            report = run_pipeline(root=root, run_id="quick-check", query="guardrails", mode="confirm_write", audit_level="quick")
            self.assertEqual(report.get("audit_level"), "quick")
            summary = report.get("incremental_summary", [])
            self.assertEqual(len(summary), 3)


if __name__ == "__main__":
    unittest.main()

