import json
import tempfile
import unittest
from pathlib import Path

from site_ops.orchestrator import OrchestratorConfig, run_orchestration


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


class SitePublishingOrchestratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        _write_json(
            self.root / "site_ops" / "config" / "agent-registry.json",
            {
                "required_agents": [
                    "orchestrator",
                    "strategy_agent",
                    "content_agent",
                    "seo_agent",
                    "ui_stitch_agent",
                    "implementation_agent",
                    "qa_agent",
                    "release_agent",
                    "analytics_agent",
                ],
                "default_flow": [
                    "strategy_agent",
                    "content_agent",
                    "seo_agent",
                    "ui_stitch_agent",
                    "implementation_agent",
                    "qa_agent",
                    "release_agent",
                    "analytics_agent",
                ],
            },
        )
        _write_json(
            self.root / "site_ops" / "config" / "publishing-policy.json",
            {
                "preview_only_default": True,
                "require_confirmation_for_release": True,
                "require_confirmation_for_output_write": True,
                "required_quality_gates": [
                    "content_review_passed",
                    "seo_review_passed",
                    "ui_review_passed",
                    "qa_review_passed",
                ],
            },
        )
        _write_json(
            self.root / "site_ops" / "config" / "stitch-integration.json",
            {
                "enabled": True,
                "tool": "google-stitch",
                "ui_owner_agent": "ui_stitch_agent",
            },
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_preview_mode(self) -> None:
        report = run_orchestration(
            OrchestratorConfig(root_dir=self.root, run_id="run-preview", confirm_writes=False)
        )
        self.assertEqual(report["status"], "needs_confirmation")
        names = [item["agent"] for item in report["agent_results"]]
        self.assertIn("ui_stitch_agent", names)

    def test_confirm_write_persists_output(self) -> None:
        report = run_orchestration(
            OrchestratorConfig(root_dir=self.root, run_id="run-confirm", confirm_writes=True)
        )
        self.assertEqual(report["status"], "done")
        output = self.root / "site_ops" / "output" / "site-flow-run-confirm.json"
        self.assertTrue(output.exists())


if __name__ == "__main__":
    unittest.main()
