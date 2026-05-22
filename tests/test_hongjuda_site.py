import base64
import io
import json
import tempfile
import unittest
from pathlib import Path
from urllib.parse import urlsplit

from hongjuda_site.local_server import create_app


ROOT = Path(__file__).resolve().parents[1]
SITE_DIR = ROOT / "hongjuda_site"


def _request(app, method: str, path: str, body: bytes = b"", headers: dict[str, str] | None = None):
    parsed = urlsplit(path)
    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": parsed.path,
        "QUERY_STRING": parsed.query,
        "wsgi.input": io.BytesIO(body),
        "CONTENT_LENGTH": str(len(body)),
    }
    for key, value in (headers or {}).items():
        environ[f"HTTP_{key.upper().replace('-', '_')}"] = value
    status_holder = {}
    chunks = []

    def start_response(status, response_headers):
        status_holder["status"] = status
        status_holder["headers"] = dict(response_headers)

    for chunk in app(environ, start_response):
        chunks.append(chunk)
    return int(status_holder["status"].split()[0]), status_holder["headers"], b"".join(chunks)


class HongjudaSiteTests(unittest.TestCase):
    def test_static_site_has_company_content_and_llm_discovery(self):
        index_html = (SITE_DIR / "index.html").read_text(encoding="utf-8")
        llms = (SITE_DIR / "llms.txt").read_text(encoding="utf-8")
        content = json.loads((SITE_DIR / "content" / "site-content.json").read_text(encoding="utf-8"))

        self.assertIn("苏州宏聚达装饰材料有限公司", index_html)
        self.assertIn("SuZhou hongjuda decorative material co.,ltd", index_html)
        self.assertIn('id="products"', index_html)
        self.assertIn('id="cases"', index_html)
        self.assertIn('application/ld+json', index_html)
        self.assertIn('"@type": "Organization"', index_html)
        self.assertIn("WPC decking", llms)
        self.assertIn("acoustic slat wall panels", llms)
        self.assertEqual(content["company"]["name_zh"], "苏州宏聚达装饰材料有限公司")
        self.assertGreaterEqual(len(content["products"]), 6)
        self.assertGreaterEqual(len(content["cases"]), 4)

    def test_admin_surface_and_local_api_persist_content_and_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp_site = Path(tmp)
            for source in SITE_DIR.iterdir():
                if source.name == "__pycache__":
                    continue
                if source.is_dir():
                    import shutil

                    shutil.copytree(source, temp_site / source.name)
                else:
                    (temp_site / source.name).write_bytes(source.read_bytes())

            app = create_app(temp_site)
            status, headers, body = _request(app, "GET", "/admin.html")
            self.assertEqual(status, 200)
            self.assertIn("text/html", headers["Content-Type"])
            self.assertIn("宏聚达内容管理后台", body.decode("utf-8"))

            update = {"hero": {"title": "Updated durable surface systems"}}
            status, _, payload = _request(
                app,
                "PUT",
                "/api/content",
                body=json.dumps(update).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            self.assertEqual(status, 200)
            saved = json.loads(payload.decode("utf-8"))
            self.assertEqual(saved["hero"]["title"], "Updated durable surface systems")
            persisted = json.loads((temp_site / "content" / "site-content.json").read_text(encoding="utf-8"))
            self.assertEqual(persisted["hero"]["title"], "Updated durable surface systems")

            png_bytes = b"\x89PNG\r\n\x1a\nfake"
            status, _, payload = _request(
                app,
                "POST",
                "/api/assets",
                body=json.dumps({
                    "filename": "new hero.png",
                    "content_base64": base64.b64encode(png_bytes).decode("ascii"),
                }).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            self.assertEqual(status, 200)
            asset = json.loads(payload.decode("utf-8"))
            self.assertEqual(asset["path"], "./assets/uploads/new-hero.png")
            self.assertEqual((temp_site / "assets" / "uploads" / "new-hero.png").read_bytes(), png_bytes)


if __name__ == "__main__":
    unittest.main()
