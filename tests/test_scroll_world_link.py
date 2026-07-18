import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("scroll_world_link", ROOT / "scripts" / "scroll-world-link.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class ScrollWorldLinkTests(unittest.TestCase):
    def test_both_worktrees_have_matching_skill(self) -> None:
        config = MODULE.load_config(ROOT)
        status = MODULE.build_status(ROOT, config)
        self.assertTrue(status["local_available"])
        self.assertTrue(status["peer_available"])
        self.assertTrue(status["skill_versions_match"])

    def test_camera_chain_routes_to_video_workflow(self) -> None:
        config = MODULE.load_config(ROOT)
        handoff = MODULE.build_handoff(ROOT, config, "camera_chain", "demo", "continuous flight")
        self.assertEqual("video_workflow", handoff["target_workspace"])
        self.assertTrue(handoff["link_ready"])

    def test_site_dispatch_is_accepted_by_video_workflow(self) -> None:
        config = MODULE.load_config(ROOT)
        payload = MODULE.build_handoff(ROOT, config, "camera_chain", "demo", "continuous flight")
        response = MODULE.dispatch_handoff(ROOT, config, payload)
        self.assertEqual("accepted", response["status"])
        self.assertEqual("video_workflow", response["workspace"])


if __name__ == "__main__":
    unittest.main()
