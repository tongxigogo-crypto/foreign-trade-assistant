import base64
import io
import json
import tempfile
import unittest
from pathlib import Path
from urllib.parse import urlsplit
from unittest.mock import patch
from wsgiref.util import setup_testing_defaults

from site_backend.app import create_app
from site_backend.content_store import ContentStore
from site_backend.server import create_site_server
from site_backend.v66_adapter import apply_content


def _request(app, method: str, path: str, body: bytes = b"", headers: dict[str, str] | None = None) -> tuple[int, dict[str, str], bytes]:
    environ: dict[str, object] = {}
    setup_testing_defaults(environ)
    parsed = urlsplit(path)
    environ["REQUEST_METHOD"] = method
    environ["PATH_INFO"] = parsed.path
    environ["QUERY_STRING"] = parsed.query
    environ["wsgi.input"] = io.BytesIO(body)
    environ["CONTENT_LENGTH"] = str(len(body))
    for key, value in (headers or {}).items():
        header_key = key.upper().replace("-", "_")
        if header_key in {"CONTENT_TYPE", "CONTENT_LENGTH", "COOKIE"}:
            environ[header_key] = value
        else:
            environ[f"HTTP_{header_key}"] = value

    status_holder: dict[str, object] = {}
    chunks: list[bytes] = []

    def start_response(status: str, response_headers: list[tuple[str, str]]):
        status_holder["status"] = status
        status_holder["headers"] = response_headers

    for chunk in app(environ, start_response):
        chunks.append(chunk)

    status_code = int(str(status_holder["status"]).split()[0])
    response_headers = {key: value for key, value in status_holder["headers"]}  # type: ignore[index]
    return status_code, response_headers, b"".join(chunks)


class SiteBackendTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.site_dir = self.root / "website_from_playground"
        (self.site_dir / "assets").mkdir(parents=True, exist_ok=True)
        (self.site_dir / "index.html").write_text("<!doctype html><title>Site</title>", encoding="utf-8")
        self.app = create_app(
            root_dir=self.root,
            admin_password="secret-pass",
            session_secret="session-secret",
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _login_cookie(self) -> str:
        body = json.dumps({"password": "secret-pass"}).encode("utf-8")
        status, headers, _ = _request(
            self.app,
            "POST",
            "/admin/api/login",
            body=body,
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(status, 200)
        self.assertIn("Set-Cookie", headers)
        return headers["Set-Cookie"].split(";", 1)[0]

    def test_public_content_endpoint_returns_default_document(self) -> None:
        status, headers, payload = _request(self.app, "GET", "/api/content")

        self.assertEqual(status, 200)
        self.assertEqual(headers["Content-Type"], "application/json; charset=utf-8")
        data = json.loads(payload.decode("utf-8"))
        self.assertIn("strings", data)
        self.assertIn("images", data)
        self.assertIn("zh", data["strings"])
        self.assertIn("en", data["strings"])
        self.assertIn("zh", data["pet_products_gallery"])
        self.assertIn("en", data["pet_products_gallery"])

    def test_content_store_accepts_utf8_bom_json_files(self) -> None:
        content_dir = self.site_dir / "content"
        content_dir.mkdir(parents=True, exist_ok=True)
        (content_dir / "site-content.json").write_text(
            '\ufeff{"strings":{"en":{"hero_intro":"BOM safe"}}}',
            encoding="utf-8",
        )

        data = ContentStore(self.site_dir).load()

        self.assertEqual(data["strings"]["en"]["hero_intro"], "BOM safe")

    def test_site_server_requires_explicit_admin_credentials(self) -> None:
        with patch.dict(
            "os.environ",
            {
                "SITE_ADMIN_PASSWORD": "",
                "SITE_ADMIN_SESSION_SECRET": "",
                "SITE_ALLOW_INSECURE_DEFAULT_ADMIN": "",
            },
            clear=False,
        ):
            with self.assertRaisesRegex(RuntimeError, "SITE_ADMIN_PASSWORD must be set"):
                create_site_server(self.root)

    def test_public_ai_context_endpoint_exposes_assistant_contract(self) -> None:
        status, headers, payload = _request(self.app, "GET", "/api/ai-context")

        self.assertEqual(status, 200)
        self.assertEqual(headers["Content-Type"], "application/json; charset=utf-8")
        self.assertEqual(headers["Access-Control-Allow-Origin"], "*")
        data = json.loads(payload.decode("utf-8"))
        self.assertEqual(data["ai_core"]["id"], "douzi-core")
        self.assertEqual(data["ai_core"]["message_endpoint"], "/api/ai-core/message")
        self.assertEqual(data["product"]["version"], "v0.1.1 Beta")
        self.assertIn("en", data["site"]["languages"])
        self.assertIn("zh", data["site"]["languages"])

    def test_ai_core_message_endpoint_is_reserved_without_model_call(self) -> None:
        body = json.dumps({"message": "How can this site help with quotes?", "locale": "en"}).encode("utf-8")
        status, headers, payload = _request(
            self.app,
            "POST",
            "/api/ai-core/message",
            body=body,
            headers={"Content-Type": "application/json"},
        )

        self.assertEqual(status, 200)
        self.assertEqual(headers["Access-Control-Allow-Origin"], "*")
        data = json.loads(payload.decode("utf-8"))
        self.assertTrue(data["ok"])
        self.assertEqual(data["assistant"]["id"], "douzi-core")
        self.assertFalse(data["assistant"]["model_connected"])
        self.assertEqual(data["status"], "reserved")
        self.assertTrue(data["input_received"])

    def test_contact_endpoint_accepts_valid_placeholder_submission(self) -> None:
        body = json.dumps({
            "name": "Alex Buyer",
            "contact": "alex@example.com",
            "intent": "website-development",
            "message": "We need a pet product landing page and want to discuss the first scope.",
            "locale": "en",
            "company_url": "",
        }).encode("utf-8")

        status, headers, payload = _request(
            self.app,
            "POST",
            "/api/contact",
            body=body,
            headers={"Content-Type": "application/json"},
        )

        self.assertEqual(status, 202)
        self.assertEqual(headers["Access-Control-Allow-Origin"], "*")
        data = json.loads(payload.decode("utf-8"))
        self.assertTrue(data["ok"])
        self.assertEqual(data["status"], "feed_saved")
        self.assertEqual(data["email_to"], "tongxigogo@gmail.com")
        self.assertEqual(data["submission"]["intent"], "website-development")
        submission_path = self.site_dir / "content" / "contact-submissions.jsonl"
        self.assertTrue(submission_path.exists())
        rows = [json.loads(line) for line in submission_path.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(rows[0]["contact"], "alex@example.com")
        self.assertEqual(rows[0]["intent"], "website-development")

    def test_contact_endpoint_rejects_invalid_or_spam_submission(self) -> None:
        invalid = json.dumps({"name": "A", "contact": "", "intent": "bad", "message": "short"}).encode("utf-8")
        status, _, payload = _request(
            self.app,
            "POST",
            "/api/contact",
            body=invalid,
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(status, 400)
        self.assertFalse(json.loads(payload.decode("utf-8"))["ok"])

        spam = json.dumps({
            "name": "Spam Bot",
            "contact": "bot@example.com",
            "intent": "ip-collaboration",
            "message": "This should be ignored by honeypot filtering.",
            "company_url": "https://spam.example",
        }).encode("utf-8")
        status, _, payload = _request(
            self.app,
            "POST",
            "/api/contact",
            body=spam,
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(payload.decode("utf-8"))["status"], "ignored")
        self.assertFalse((self.site_dir / "content" / "contact-submissions.jsonl").exists())

    def test_admin_contact_submissions_requires_auth_and_returns_recent_items(self) -> None:
        body = json.dumps({
            "name": "Alex Buyer",
            "contact": "alex@example.com",
            "intent": "product-information",
            "message": "Need product information.",
            "locale": "en",
            "company_url": "",
        }).encode("utf-8")
        _request(self.app, "POST", "/api/contact", body=body, headers={"Content-Type": "application/json"})

        status, _, _ = _request(self.app, "GET", "/admin/api/contact-submissions")
        self.assertEqual(status, 401)

        cookie = self._login_cookie()
        status, _, payload = _request(self.app, "GET", "/admin/api/contact-submissions", headers={"Cookie": cookie})
        self.assertEqual(status, 200)
        data = json.loads(payload.decode("utf-8"))
        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(data["items"][0]["intent"], "product-information")
        self.assertEqual(data["items"][0]["contact"], "alex@example.com")

    def test_admin_meta_endpoint_returns_history_shape(self) -> None:
        cookie = self._login_cookie()
        status, _, payload = _request(self.app, "GET", "/admin/api/meta", headers={"Cookie": cookie})
        self.assertEqual(status, 200)
        data = json.loads(payload.decode("utf-8"))
        self.assertIn("updated_at", data)
        self.assertIn("history", data)

    def test_publish_endpoint_records_publish_history(self) -> None:
        cookie = self._login_cookie()
        status, _, payload = _request(self.app, "POST", "/admin/api/publish", body=b"{}", headers={
            "Content-Type": "application/json",
            "Cookie": cookie,
        })
        self.assertEqual(status, 200)
        data = json.loads(payload.decode("utf-8"))
        self.assertTrue(data["updated_at"])
        self.assertEqual(data["history"][0]["event"], "content_published")

    def test_admin_content_requires_auth(self) -> None:
        status, _, _ = _request(self.app, "GET", "/admin/api/content")
        self.assertEqual(status, 401)

    def test_login_sets_session_cookie_and_token(self) -> None:
        body = json.dumps({"password": "secret-pass"}).encode("utf-8")
        status, headers, payload = _request(
            self.app,
            "POST",
            "/admin/api/login",
            body=body,
            headers={"Content-Type": "application/json"},
        )

        self.assertEqual(status, 200)
        self.assertIn("Set-Cookie", headers)
        self.assertIn("site_admin_session=", headers["Set-Cookie"])
        data = json.loads(payload.decode("utf-8"))
        self.assertTrue(data["ok"])
        self.assertTrue(data["token"])

    def test_token_auth_can_open_admin_and_save_content(self) -> None:
        body = json.dumps({"password": "secret-pass"}).encode("utf-8")
        status, _, payload = _request(
            self.app,
            "POST",
            "/admin/api/login",
            body=body,
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(status, 200)
        token = json.loads(payload.decode("utf-8"))["token"]

        status, _, body = _request(self.app, "GET", f"/admin?token={token}")
        self.assertEqual(status, 200)
        self.assertIn("Site Content Admin", body.decode("utf-8"))

        update = {
            "strings": {"en": {"hero_intro": "Token update"}},
            "images": {"home.hero": "./assets/uploads/token.png"},
        }
        status, _, body = _request(
            self.app,
            "PUT",
            "/admin/api/content",
            body=json.dumps(update).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
        )
        self.assertEqual(status, 200)
        saved = json.loads(body.decode("utf-8"))
        self.assertEqual(saved["strings"]["en"]["hero_intro"], "Token update")

    def test_authenticated_content_update_persists_json(self) -> None:
        cookie = self._login_cookie()
        payload = {
            "strings": {
                "zh": {"hero_intro": "新的中文首页说明"},
                "en": {"hero_intro": "Updated home intro"},
            },
            "images": {"home.hero": "./assets/uploads/new-hero.png"},
            "pet_products_gallery": {
                "cards": [
                    {
                        "id": "harness",
                        "image": "./assets/uploads/harness.png",
                        "cover_label": "Harness Guide",
                        "cover_title": "胸背带",
                        "title": "胸背带内容位",
                        "summary": "后续会补入材质、尺寸、MOQ 与适用场景。",
                        "tag": "Material / MOQ",
                        "status": "coming_soon",
                    }
                ]
            },
            "pet_product_template": {
                "title": "宠物用品内容模板",
                "intro": "先用一套统一模板承接后续内容。",
                "sections": {
                    "story_title": "产品故事",
                    "story_body": "这里放产品定位、材质选择和适用场景。",
                    "spec_title": "规格与沟通点",
                    "spec_body": "这里放 MOQ、尺寸、五金、包装等信息。",
                    "use_case_title": "使用场景",
                    "use_case_body": "这里放宠物使用环境和图文建议。",
                },
                "seo": {
                    "title": "Tong工作室 | 宠物用品内容模板",
                    "description": "宠物用品内容模板 SEO 描述",
                },
            },
        }
        status, _, _ = _request(
            self.app,
            "PUT",
            "/admin/api/content",
            body=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Cookie": cookie,
            },
        )
        self.assertEqual(status, 200)

        status, _, body = _request(self.app, "GET", "/admin/api/content", headers={"Cookie": cookie})
        self.assertEqual(status, 200)
        data = json.loads(body.decode("utf-8"))
        self.assertEqual(data["strings"]["zh"]["hero_intro"], "新的中文首页说明")
        self.assertEqual(data["images"]["home.hero"], "./assets/uploads/new-hero.png")
        self.assertEqual(data["pet_products_gallery"]["cards"][0]["title"], "胸背带内容位")
        self.assertEqual(data["pet_products_gallery"]["cards"][0]["status"], "coming_soon")
        self.assertEqual(data["pet_product_template"]["seo"]["description"], "宠物用品内容模板 SEO 描述")

        content_file = self.site_dir / "content" / "site-content.json"
        self.assertTrue(content_file.exists())
        persisted = json.loads(content_file.read_text(encoding="utf-8"))
        self.assertEqual(persisted["strings"]["en"]["hero_intro"], "Updated home intro")
        self.assertEqual(persisted["pet_products_gallery"]["cards"][0]["image"], "./assets/uploads/harness.png")
        self.assertEqual(persisted["pet_products_gallery"]["zh"]["cards"][0]["image"], "./assets/uploads/harness.png")
        self.assertIn("cards", persisted["pet_products_gallery"]["en"])
        self.assertEqual(persisted["pet_product_template"]["sections"]["spec_title"], "规格与沟通点")
        meta_file = self.site_dir / "content" / "site-content.meta.json"
        self.assertTrue(meta_file.exists())
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        self.assertTrue(meta["updated_at"])
        self.assertGreaterEqual(len(meta["history"]), 1)

    def test_extended_gallery_and_template_fields_persist_and_generate_discovery_files(self) -> None:
        cookie = self._login_cookie()
        payload = {
            "pet_products_gallery": {
                "cards": [
                    {
                        "id": "harness",
                        "image": "./assets/uploads/harness.png",
                        "cover_label": "Harness Guide",
                        "cover_title": "Harness",
                        "title": "Harness spotlight",
                        "summary": "Lightweight homepage summary",
                        "tag": "Material / MOQ",
                        "status": "live",
                        "entry_mode": "template",
                    }
                ]
            },
            "pet_product_template": {
                "path": "./pet-product-template.html",
                "eyebrow": "Pet Product Template",
                "title": "Pet Product Content Template",
                "intro": "Use one shared template before detailed product pages go live.",
                "status_label": "Template Preview",
                "cta_label": "Contact for Inquiry",
                "cta_url": "mailto:tongxigogo@gmail.com",
                "sections": {
                    "story_title": "Product Story",
                    "story_body": "Explain the product role and editorial angle.",
                    "spec_title": "Specs & Notes",
                    "spec_body": "MOQ, packaging, and quote-facing details.",
                    "use_case_title": "Use Case",
                    "use_case_body": "How this product is used in pet scenarios.",
                    "care_title": "Care & Notes",
                    "care_body": "Cleaning and sales reminders.",
                },
                "specs": [
                    {"label": "MOQ", "value": "300 sets"},
                    {"label": "Material", "value": "Oxford fabric"},
                    {"label": "Packaging", "value": "Flat pack"},
                ],
                "seo": {
                    "title": "Tong Studio | Pet Product Template",
                    "description": "Template page for upcoming pet product detail content.",
                    "canonical_path": "/pet-product-template.html",
                },
            },
        }
        status, _, _ = _request(
            self.app,
            "PUT",
            "/admin/api/content",
            body=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Cookie": cookie,
            },
        )
        self.assertEqual(status, 200)

        content_file = self.site_dir / "content" / "site-content.json"
        persisted = json.loads(content_file.read_text(encoding="utf-8"))
        first_card = persisted["pet_products_gallery"]["cards"][0]
        self.assertEqual(first_card["entry_mode"], "template")
        template = persisted["pet_product_template"]
        self.assertEqual(template["eyebrow"], "Pet Product Template")
        self.assertEqual(template["status_label"], "Template Preview")
        self.assertEqual(template["cta_url"], "mailto:tongxigogo@gmail.com")
        self.assertEqual(template["sections"]["care_title"], "Care & Notes")
        self.assertEqual(template["specs"][1]["value"], "Oxford fabric")
        self.assertEqual(template["seo"]["canonical_path"], "/pet-product-template.html")

        robots = (self.site_dir / "robots.txt").read_text(encoding="utf-8")
        sitemap = (self.site_dir / "sitemap.xml").read_text(encoding="utf-8")
        self.assertIn("Sitemap:", robots)
        self.assertIn("pet-product-template.html", sitemap)

        rendered = apply_content('<div class="pet-gallery-row">old</div>\n\n                    <div class="pet-gallery-note">', payload)
        self.assertIn('href="./pet-product-template.html#harness"', rendered)
        self.assertIn('class="pet-gallery-card" data-poster-href="./pet-product-template.html#harness"', rendered)
        self.assertIn('class="pet-gallery-image-link" href="./pet-product-template.html#harness"', rendered)
        self.assertNotIn("View poster", rendered)
        self.assertNotIn("pet-gallery-footer", rendered)
        self.assertNotIn("Lightweight homepage summary", rendered)

    def test_bilingual_gallery_fields_persist_with_legacy_zh_mirror(self) -> None:
        cookie = self._login_cookie()
        payload = {
            "pet_products_gallery": {
                "zh": {
                    "cards": [
                        {
                            "id": "harness",
                            "image": "./assets/uploads/zh-harness.png",
                            "cover_label": "胸背指南",
                            "cover_title": "胸背带",
                            "title": "中文胸背带",
                            "summary": "中文摘要",
                            "tag": "材质 / MOQ",
                            "status": "coming_soon",
                            "entry_mode": "template",
                        }
                    ]
                },
                "en": {
                    "cards": [
                        {
                            "id": "harness",
                            "image": "./assets/uploads/en-harness.png",
                            "cover_label": "Harness Guide",
                            "cover_title": "Harness",
                            "title": "English harness",
                            "summary": "English summary",
                            "tag": "Material / MOQ",
                            "status": "live",
                            "entry_mode": "template",
                        }
                    ]
                },
            }
        }
        status, _, _ = _request(
            self.app,
            "PUT",
            "/admin/api/content",
            body=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Cookie": cookie,
            },
        )
        self.assertEqual(status, 200)

        persisted = json.loads((self.site_dir / "content" / "site-content.json").read_text(encoding="utf-8"))
        self.assertEqual(persisted["pet_products_gallery"]["zh"]["cards"][0]["title"], "中文胸背带")
        self.assertEqual(persisted["pet_products_gallery"]["en"]["cards"][0]["title"], "English harness")
        self.assertEqual(persisted["pet_products_gallery"]["cards"][0]["title"], "中文胸背带")
        rendered = apply_content('<div class="pet-gallery-row">old</div>\n\n                    <div class="pet-gallery-note">', payload)
        self.assertIn("English harness", rendered)
        self.assertIn('href="./pet-product-template.html#harness"', rendered)
        self.assertIn('data-poster-href="./pet-product-template.html#harness"', rendered)
        self.assertNotIn("pet-gallery-footer", rendered)

    def test_asset_upload_writes_file_and_returns_relative_path(self) -> None:
        cookie = self._login_cookie()
        png_bytes = b"\x89PNG\r\n\x1a\nfake-image"
        payload = {
            "filename": "hero.png",
            "content_base64": base64.b64encode(png_bytes).decode("ascii"),
        }
        status, _, body = _request(
            self.app,
            "POST",
            "/admin/api/assets",
            body=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Cookie": cookie,
            },
        )

        self.assertEqual(status, 200)
        data = json.loads(body.decode("utf-8"))
        self.assertTrue(data["path"].startswith("./assets/uploads/"))
        saved_file = self.site_dir / data["path"].replace("./", "")
        self.assertTrue(saved_file.exists())
        self.assertEqual(saved_file.read_bytes(), png_bytes)

    def test_admin_page_renders_login_when_unauthenticated(self) -> None:
        status, headers, body = _request(self.app, "GET", "/admin")
        self.assertEqual(status, 200)
        self.assertEqual(headers["Content-Type"], "text/html; charset=utf-8")
        html = body.decode("utf-8")
        self.assertIn("Admin Login", html)
        self.assertIn("site_admin_password", html)

    def test_admin_page_renders_editor_when_authenticated(self) -> None:
        cookie = self._login_cookie()
        status, _, body = _request(self.app, "GET", "/admin", headers={"Cookie": cookie})
        self.assertEqual(status, 200)
        html = body.decode("utf-8")
        self.assertIn("Site Content Admin", html)
        self.assertIn("content-navigator", html.lower().replace("_", "-"))
        self.assertIn("图片资源", html)
        self.assertIn("宠物用品画廊", html)
        self.assertIn("详情页模板", html)
        self.assertIn("保存当前改动", html)
        self.assertIn('data-preview-target="zh"', html)
        self.assertIn('data-preview-target="en"', html)
        self.assertIn('data-preview-target="template"', html)
        self.assertIn("Preview English Home", html)
        self.assertIn("发布前检查", html)
        self.assertIn("publish-content", html)
        self.assertIn("publish-modal", html)
        self.assertIn("preview-diff", html)
        self.assertIn("preview-state", html)
        self.assertIn("preview-modal", html)
        self.assertIn("confirm-preview", html)
        self.assertIn("投喂信息", html)
        self.assertIn("contact-submissions", html)
        self.assertIn("gallery-preview-rail", html)
        self.assertIn("Homepage Gallery Preview", html)


if __name__ == "__main__":
    unittest.main()
