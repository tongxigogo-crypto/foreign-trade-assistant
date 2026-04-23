import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE_DIR = ROOT / "website_from_playground"
EXTERNAL_V66 = Path(r"C:\Users\Administrator\Desktop\preson\indexV6.6_refined.html")
EXTERNAL_TEMPLATE = Path(r"C:\Users\Administrator\Desktop\preson\pet-product-template.html")


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
        suspicious_markers = ["鐎", "閸", "妫", "閼", "鈧"]
        expected_zh = ["宠物", "联系", "外贸助理", "国际贸易", "小程序开发"]

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

    def test_external_v66_has_core_seo_semantics(self) -> None:
        html = EXTERNAL_V66.read_text(encoding="utf-8")

        self.assertIn('<meta name="description"', html)
        self.assertIn('<link rel="canonical"', html)
        self.assertIn('application/ld+json', html)
        self.assertIn('SoftwareApplication', html)
        self.assertIn('aria-label="把客户、报价、邮件和任务收回同一个工作台"', html)
        self.assertIn('alt="豆子核心 - 短尾巴柯基 3D 角色头像，代表系统底层逻辑与全局避障引擎"', html)
        self.assertIn('alt="外贸助理 APP v0.1.1 界面，展示本地优先的客户询盘分析、多模型兼容与报价跟进工作流"', html)
        self.assertIn('fetchpriority="high"', html)
        self.assertIn('loading="lazy"', html)

    def test_external_v66_has_pet_products_gallery_section(self) -> None:
        html = EXTERNAL_V66.read_text(encoding="utf-8")

        self.assertIn('id="pet-products-gallery"', html)
        self.assertIn("Pet Product Stories", html)
        self.assertIn("Pet Products / Editorial Gallery", html)
        self.assertIn("grid-auto-flow: column", html)
        self.assertIn("overflow-x: auto", html)
        self.assertIn("scrollbar-width: none", html)
        self.assertIn("function initPetGalleryRail()", html)
        self.assertGreaterEqual(html.count('class="pet-gallery-card"'), 4)
        self.assertGreaterEqual(html.count('class="pet-gallery-image"'), 4)
        self.assertIn('class="use-pretext" style="color: #0F172A;">', html)
        self.assertGreaterEqual(html.count('class="pet-gallery-link is-coming"'), 4)
        self.assertIn('href="./pet-product-template.html"', html)
        self.assertNotIn("鏌ョ湅璇︽儏", html)

    def test_external_v66_uses_consistent_section_shells(self) -> None:
        html = EXTERNAL_V66.read_text(encoding="utf-8")

        self.assertIn("--content-shell: 1400px", html)
        self.assertIn("max-width: var(--content-shell)", html)
        self.assertGreaterEqual(html.count("section-shell"), 4)

    def test_external_pet_product_template_has_basic_seo_shell(self) -> None:
        html = EXTERNAL_TEMPLATE.read_text(encoding="utf-8")

        self.assertIn('<meta name="description"', html)
        self.assertIn('<link rel="canonical"', html)
        self.assertIn('application/ld+json', html)
        self.assertIn('Pet Product Template', html)
        self.assertIn('/api/content', html)
        self.assertIn('product-hero-image', html)
        self.assertIn('product-eyebrow', html)
        self.assertIn('primary-cta', html)
        self.assertIn('spec-label-0', html)
        self.assertIn('care-title', html)


if __name__ == "__main__":
    unittest.main()
