import unittest
import tempfile
from pathlib import Path

from agent_system.harness.workflow_engine import (
    HarnessPaths,
    build_closed_loop_verdict,
    build_preflight_report,
    checkpoint_session,
)


class WorkflowEngineTests(unittest.TestCase):
    def test_preflight_blocked_when_required_agent_missing(self) -> None:
        report = build_preflight_report(
            required_agents=["orchestrator_agent", "review_agent"],
            required_outputs=["run_report"],
            planned_outputs={"run_report": "x.json"},
            agent_results=[
                {
                    "agent": "orchestrator_agent",
                    "status": "done",
                    "payload": {},
                    "missing_data": [],
                }
            ],
        )
        self.assertEqual(report["status"], "blocked")
        self.assertTrue(any("missing required agents" in item for item in report["violations"]))

    def test_closed_loop_preview_status(self) -> None:
        verdict = build_closed_loop_verdict(
            run_status="needs_confirmation",
            checks=[{"name": "preflight_ok", "passed": True}],
            evidence={},
        )
        self.assertEqual(verdict["status"], "preview")

    def test_checkpoint_roundtrip_writes_json_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = HarnessPaths(
                session_state=root / "docs" / "harness" / "session_state.json",
                current_session=root / "docs" / "harness" / "current_session.md",
                guardrail_report=root / "docs" / "harness" / "architecture_guardrails.json",
                closed_loop_verdict=root / "docs" / "harness" / "closed_loop_verdict.json",
                run_reports_dir=root / "agent_system" / "output",
            )
            checkpoint_session(
                paths,
                active_task="task-a",
                current_goal="goal-a",
                progress=["p1", "p2"],
                next_actions=["n1", "n2"],
                blockers=[],
                summary="summary-a",
                git_status="M foo.py",
            )
            self.assertTrue(paths.session_state.exists())
            self.assertTrue(paths.current_session.exists())
            session_payload = paths.session_state.read_text(encoding="utf-8")
            self.assertIn("task-a", session_payload)
            self.assertIn("M foo.py", session_payload)
            current_md = paths.current_session.read_text(encoding="utf-8")
            self.assertIn("goal-a", current_md)
            self.assertIn("summary-a", current_md)


if __name__ == "__main__":
    unittest.main()
