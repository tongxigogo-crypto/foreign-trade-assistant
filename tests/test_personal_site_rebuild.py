import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE_DIR = ROOT / "website_from_playground"


class PersonalSiteRebuildTests(unittest.TestCase):
    def test_homepage_uses_new_four_entry_layout(self) -> None:
        index_html = (SITE_DIR / "index.html").read_text(encoding="utf-8")

        self.assertIn('data-home-layout="alternating-story"', index_html)
        self.assertIn('data-entry="pet-ip"', index_html)
        self.assertIn('data-entry="trade-assistant"', index_html)
        self.assertIn('data-entry="pet-trade"', index_html)
        self.assertIn('data-entry="mini-program"', index_html)
        self.assertEqual(index_html.count('data-entry="pet-ip"'), 1)
        self.assertIn('id="contact-me"', index_html)
        self.assertIn('href="#contact-me"', index_html)
        self.assertIn('favicon.svg', index_html)

    def test_homepage_states_ip_trade_relationship(self) -> None:
        index_html = (SITE_DIR / "index.html").read_text(encoding="utf-8")

        self.assertIn("为后续宠物用品国际贸易做准备", index_html)

    def test_pages_and_i18n_do_not_contain_mojibake(self) -> None:
        suspicious_markers = ["瀹", "鍥", "棣", "鑱", "€"]
        expected_zh = ["宠物", "联系我", "外贸助理", "国际贸易", "小程序开发"]

        for relative_path in [
            "index.html",
            "download.html",
            "docs.html",
            "privacy.html",
            "app.js",
        ]:
            content = (SITE_DIR / relative_path).read_text(encoding="utf-8")
            for marker in suspicious_markers:
                self.assertNotIn(marker, content, msg=f"{relative_path} still contains mojibake marker {marker!r}")
            for needle in expected_zh:
                self.assertIn(needle, content, msg=f"{relative_path} is missing expected Chinese text {needle!r}")

    def test_pretext_is_loaded_for_key_headings(self) -> None:
        index_html = (SITE_DIR / "index.html").read_text(encoding="utf-8")

        self.assertIn('type="module"', index_html)
        self.assertIn("./vendor/pretext/layout.js", index_html)
        self.assertIn('data-pretext="hero-title"', index_html)

    def test_homepage_is_ready_for_backend_managed_content(self) -> None:
        index_html = (SITE_DIR / "index.html").read_text(encoding="utf-8")
        app_js = (SITE_DIR / "app.js").read_text(encoding="utf-8")
        content_json = (SITE_DIR / "content" / "site-content.json").read_text(encoding="utf-8")

        self.assertIn('data-managed-image="home.hero"', index_html)
        self.assertIn('data-managed-image="home.trade_assistant"', index_html)
        self.assertIn('data-managed-image="home.pet_trade"', index_html)
        self.assertIn('data-managed-image="home.mini_program"', index_html)
        self.assertIn("/api/content", app_js)
        self.assertIn("hero_intro", content_json)

    def test_local_preview_script_exists(self) -> None:
        script = (SITE_DIR / "start-local.bat").read_text(encoding="utf-8")

        self.assertIn("http.server", script)
        self.assertIn("8123", script)

    def test_site_discovery_files_match_rebuild_scope(self) -> None:
        llms = (SITE_DIR / "llms.txt").read_text(encoding="utf-8")
        agent = (SITE_DIR / ".well-known" / "agent.json").read_text(encoding="utf-8")
        openapi = (SITE_DIR / "api" / "openapi.json").read_text(encoding="utf-8")

        self.assertIn("Tongxi Fairy Lab", llms)
        self.assertIn("个人网站", llms)
        self.assertIn("Tongxi Fairy Lab", agent)
        self.assertIn("site profile", openapi.lower())


if __name__ == "__main__":
    unittest.main()
