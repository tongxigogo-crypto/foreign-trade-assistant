import base64
import io
import json
import tempfile
import unittest
from pathlib import Path
from urllib.parse import urlsplit
from wsgiref.util import setup_testing_defaults

from site_backend.app import create_app


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

        content_file = self.site_dir / "content" / "site-content.json"
        self.assertTrue(content_file.exists())
        persisted = json.loads(content_file.read_text(encoding="utf-8"))
        self.assertEqual(persisted["strings"]["en"]["hero_intro"], "Updated home intro")
        meta_file = self.site_dir / "content" / "site-content.meta.json"
        self.assertTrue(meta_file.exists())
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        self.assertTrue(meta["updated_at"])
        self.assertGreaterEqual(len(meta["history"]), 1)

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
        self.assertIn("保存当前改动", html)
        self.assertIn("预览首页", html)
        self.assertIn("发布前检查", html)
        self.assertIn("publish-content", html)
        self.assertIn("publish-modal", html)
        self.assertIn("preview-diff", html)


if __name__ == "__main__":
    unittest.main()
