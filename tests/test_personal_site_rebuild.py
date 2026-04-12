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

    def test_homepage_states_ip_trade_relationship(self) -> None:
        index_html = (SITE_DIR / "index.html").read_text(encoding="utf-8")

        self.assertIn("为后续宠物用品国际贸易做准备", index_html)

    def test_pretext_is_loaded_for_key_headings(self) -> None:
        index_html = (SITE_DIR / "index.html").read_text(encoding="utf-8")

        self.assertIn('type="module"', index_html)
        self.assertIn("./vendor/pretext/layout.js", index_html)
        self.assertIn('data-pretext="hero-title"', index_html)


if __name__ == "__main__":
    unittest.main()
