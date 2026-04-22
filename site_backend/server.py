from __future__ import annotations

import mimetypes
import os
from pathlib import Path
from typing import Callable, Iterable
from wsgiref.simple_server import make_server

from .app import create_app
from .content_store import ContentStore
from .v66_adapter import PREVIEW_SCRIPT, V66_DEFAULT_CONTENT, apply_content, extract_content

StartResponse = Callable[[str, list[tuple[str, str]]], None]


def create_site_server(root_dir: Path, admin_password: str | None = None, session_secret: str | None = None):
    external_site_dir = Path(os.environ.get("SITE_MANAGED_DIR", r"C:\Users\Administrator\Desktop\preson"))
    external_index = Path(os.environ.get("SITE_MANAGED_HTML", str(external_site_dir / "indexV6.6_refined.html")))
    resolved_password = admin_password or os.environ.get("SITE_ADMIN_PASSWORD", "change-me")
    resolved_secret = session_secret or os.environ.get("SITE_ADMIN_SESSION_SECRET", "local-session-secret")
    store = ContentStore(
        external_site_dir,
        default_content=V66_DEFAULT_CONTENT,
        source_html_path=external_index,
        extract_callback=extract_content,
        sync_callback=apply_content,
    )
    backend_app = create_app(
        root_dir=root_dir,
        admin_password=resolved_password,
        session_secret=resolved_secret,
        site_dir=external_site_dir,
        default_content=V66_DEFAULT_CONTENT,
        source_html_path=external_index,
        extract_callback=extract_content,
        sync_callback=apply_content,
    )

    def app(environ: dict, start_response: StartResponse) -> Iterable[bytes]:
        path = str(environ.get("PATH_INFO", "/"))
        if path.startswith("/api/") or path == "/admin" or path.startswith("/admin/"):
            return backend_app(environ, start_response)

        relative = external_index.name if path in {"", "/"} else path.lstrip("/")
        target = (external_site_dir / relative).resolve()
        try:
            target.relative_to(external_site_dir.resolve())
        except ValueError:
            return _text_response(start_response, "403 Forbidden", "Forbidden")
        if not target.exists() or not target.is_file():
            return _text_response(start_response, "404 Not Found", "Not Found")

        if target == external_index:
            body_text = target.read_text(encoding="utf-8")
            managed_html = apply_content(body_text, store.load())
            managed_html = managed_html.replace("</body>", PREVIEW_SCRIPT + "\n</body>")
            body = managed_html.encode("utf-8")
        else:
            body = target.read_bytes()
        content_type, _ = mimetypes.guess_type(str(target))
        start_response(
            "200 OK",
            [
                ("Content-Type", content_type or "application/octet-stream"),
                ("Content-Length", str(len(body))),
            ],
        )
        return [body]

    return app


def _text_response(start_response: StartResponse, status: str, body_text: str) -> Iterable[bytes]:
    body = body_text.encode("utf-8")
    start_response(
        status,
        [
            ("Content-Type", "text/plain; charset=utf-8"),
            ("Content-Length", str(len(body))),
        ],
    )
    return [body]


def main() -> None:
    root_dir = Path(__file__).resolve().parents[1]
    host = os.environ.get("SITE_ADMIN_HOST", "127.0.0.1")
    port = int(os.environ.get("SITE_ADMIN_PORT", "8133"))
    app = create_site_server(root_dir)
    with make_server(host, port, app) as server:
        print(f"Serving site + admin at http://{host}:{port}")
        server.serve_forever()


if __name__ == "__main__":
    main()
