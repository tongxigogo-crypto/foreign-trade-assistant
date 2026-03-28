import unittest

from agent_system.harness.workflow_engine import build_closed_loop_verdict, build_preflight_report


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


if __name__ == "__main__":
    unittest.main()
