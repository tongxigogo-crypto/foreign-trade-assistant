from __future__ import annotations

import json
from http import HTTPStatus
from pathlib import Path
from typing import Callable, Iterable

from .auth import COOKIE_NAME, build_session_value, is_authenticated
from .content_store import ContentStore

StartResponse = Callable[[str, list[tuple[str, str]]], None]


def _json_response(start_response: StartResponse, status: HTTPStatus, payload: dict | None = None, headers: list[tuple[str, str]] | None = None) -> Iterable[bytes]:
    body = b""
    response_headers = [("Content-Type", "application/json; charset=utf-8")]
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    if headers:
        response_headers.extend(headers)
    response_headers.append(("Content-Length", str(len(body))))
    start_response(f"{status.value} {status.phrase}", response_headers)
    return [body]


def _html_response(start_response: StartResponse, status: HTTPStatus, html: str) -> Iterable[bytes]:
    body = html.encode("utf-8")
    start_response(
        f"{status.value} {status.phrase}",
        [
            ("Content-Type", "text/html; charset=utf-8"),
            ("Content-Length", str(len(body))),
        ],
    )
    return [body]


def _read_json(environ: dict) -> dict:
    length = int(environ.get("CONTENT_LENGTH") or "0")
    raw = environ["wsgi.input"].read(length) if length else b"{}"
    return json.loads(raw.decode("utf-8"))


def _authed(cookie_header: object, admin_password: str, session_secret: str) -> bool:
    return is_authenticated(cookie_header if isinstance(cookie_header, str) else None, admin_password, session_secret)


def _login_page() -> str:
    return """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Site Admin</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 0; background: #f5f7fb; color: #172033; }
      .shell { min-height: 100vh; display: grid; place-items: center; padding: 24px; }
      .card { width: min(420px, 100%); background: #fff; border-radius: 20px; padding: 28px; box-shadow: 0 24px 60px rgba(31, 47, 86, 0.14); }
      h1 { margin: 0 0 12px; font-size: 28px; }
      p { margin: 0 0 18px; line-height: 1.6; color: #53627c; }
      label { display: block; font-size: 14px; margin-bottom: 8px; font-weight: 700; }
      input { width: 100%; box-sizing: border-box; padding: 14px 16px; border-radius: 14px; border: 1px solid #cfd8e8; font-size: 16px; }
      button { margin-top: 16px; width: 100%; border: 0; border-radius: 14px; padding: 14px 16px; background: #15203a; color: #fff; font-size: 16px; cursor: pointer; }
      #login-status { min-height: 24px; margin-top: 12px; color: #b42318; font-size: 14px; }
    </style>
  </head>
  <body>
    <main class="shell">
      <section class="card">
        <h1>Admin Login</h1>
        <p>Use the site admin password to update homepage text and images.</p>
        <form id="login-form">
          <label for="site_admin_password">Password</label>
          <input id="site_admin_password" name="site_admin_password" type="password" autocomplete="current-password" required>
          <button type="submit">Enter Admin</button>
        </form>
        <div id="login-status"></div>
      </section>
    </main>
    <script>
      document.getElementById("login-form").addEventListener("submit", async (event) => {
        event.preventDefault();
        const status = document.getElementById("login-status");
        status.textContent = "";
        const password = document.getElementById("site_admin_password").value;
        const response = await fetch("/admin/api/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ password }),
        });
        if (!response.ok) {
          status.textContent = "Invalid password.";
          return;
        }
        window.location.reload();
      });
    </script>
  </body>
</html>"""


def _editor_page(content: dict) -> str:
    serialized = json.dumps(content, ensure_ascii=False, indent=2)
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Site Content Admin</title>
    <style>
      body {{ font-family: Arial, sans-serif; margin: 0; background: #eef3fb; color: #172033; }}
      .shell {{ padding: 24px; max-width: 1100px; margin: 0 auto; }}
      .card {{ background: #fff; border-radius: 22px; padding: 24px; box-shadow: 0 24px 60px rgba(31, 47, 86, 0.12); }}
      h1 {{ margin: 0 0 12px; font-size: 30px; }}
      p {{ margin: 0 0 20px; line-height: 1.6; color: #53627c; }}
      .toolbar {{ display: flex; gap: 12px; align-items: center; margin-bottom: 16px; flex-wrap: wrap; }}
      button {{ border: 0; border-radius: 14px; padding: 12px 16px; background: #15203a; color: #fff; font-size: 15px; cursor: pointer; }}
      input[type="file"] {{ max-width: 320px; }}
      textarea {{ width: 100%; min-height: 520px; box-sizing: border-box; border-radius: 18px; border: 1px solid #cfd8e8; padding: 18px; font-family: Consolas, monospace; font-size: 14px; line-height: 1.55; }}
      #save-status {{ min-height: 24px; margin-top: 12px; color: #155eef; font-size: 14px; }}
    </style>
  </head>
  <body>
    <main class="shell">
      <section class="card">
        <h1>Site Content Admin</h1>
        <p>Edit strings and managed image paths here. Changes are written to <code>website_from_playground/content/site-content.json</code>.</p>
        <div class="toolbar">
          <button id="save-content" type="button">Save Content</button>
          <input id="asset-file" type="file" accept="image/*">
          <button id="upload-asset" type="button">Upload Asset</button>
        </div>
        <textarea id="content-editor">{serialized}</textarea>
        <div id="save-status"></div>
      </section>
    </main>
    <script>
      async function saveContent() {{
        const status = document.getElementById("save-status");
        try {{
          const payload = JSON.parse(document.getElementById("content-editor").value);
          const response = await fetch("/admin/api/content", {{
            method: "PUT",
            headers: {{ "Content-Type": "application/json" }},
            body: JSON.stringify(payload),
          }});
          if (!response.ok) throw new Error("save_failed");
          const saved = await response.json();
          document.getElementById("content-editor").value = JSON.stringify(saved, null, 2);
          status.textContent = "Saved.";
        }} catch (error) {{
          status.textContent = "Save failed. Check JSON format.";
        }}
      }}

      async function uploadAsset() {{
        const input = document.getElementById("asset-file");
        const file = input.files && input.files[0];
        const status = document.getElementById("save-status");
        if (!file) {{
          status.textContent = "Choose an image first.";
          return;
        }}
        const buffer = await file.arrayBuffer();
        let binary = "";
        const bytes = new Uint8Array(buffer);
        bytes.forEach((value) => {{ binary += String.fromCharCode(value); }});
        const response = await fetch("/admin/api/assets", {{
          method: "POST",
          headers: {{ "Content-Type": "application/json" }},
          body: JSON.stringify({{
            filename: file.name,
            content_base64: btoa(binary),
          }}),
        }});
        if (!response.ok) {{
          status.textContent = "Upload failed.";
          return;
        }}
        const payload = await response.json();
        status.textContent = `Uploaded: ${{payload.path}}`;
      }}

      document.getElementById("save-content").addEventListener("click", saveContent);
      document.getElementById("upload-asset").addEventListener("click", uploadAsset);
    </script>
  </body>
</html>"""


def create_app(root_dir: Path, admin_password: str, session_secret: str):
    site_dir = root_dir / "website_from_playground"
    store = ContentStore(site_dir)

    def app(environ: dict, start_response: StartResponse) -> Iterable[bytes]:
        method = str(environ.get("REQUEST_METHOD", "GET")).upper()
        path = str(environ.get("PATH_INFO", "/"))
        cookie_header = environ.get("COOKIE")

        if method == "GET" and path == "/api/content":
            return _json_response(start_response, HTTPStatus.OK, store.load())

        if path.startswith("/admin/api/"):
            if path == "/admin/api/login" and method == "POST":
                payload = _read_json(environ)
                if payload.get("password") != admin_password:
                    return _json_response(start_response, HTTPStatus.UNAUTHORIZED, {"error": "invalid_credentials"})
                cookie_value = build_session_value(admin_password, session_secret)
                return _json_response(
                    start_response,
                    HTTPStatus.NO_CONTENT,
                    headers=[
                        ("Set-Cookie", f"{COOKIE_NAME}={cookie_value}; Path=/; HttpOnly; SameSite=Lax"),
                    ],
                )

            if not _authed(cookie_header, admin_password, session_secret):
                return _json_response(start_response, HTTPStatus.UNAUTHORIZED, {"error": "auth_required"})

            if path == "/admin/api/content" and method == "GET":
                return _json_response(start_response, HTTPStatus.OK, store.load())

            if path == "/admin/api/content" and method == "PUT":
                payload = _read_json(environ)
                saved = store.save(payload)
                return _json_response(start_response, HTTPStatus.OK, saved)

            if path == "/admin/api/assets" and method == "POST":
                payload = _read_json(environ)
                try:
                    relative_path = store.save_asset(
                        str(payload.get("filename", "")),
                        str(payload.get("content_base64", "")),
                    )
                except (ValueError, json.JSONDecodeError):
                    return _json_response(start_response, HTTPStatus.BAD_REQUEST, {"error": "invalid_asset"})
                return _json_response(start_response, HTTPStatus.OK, {"path": relative_path})

        if method == "GET" and path == "/admin":
            if not _authed(cookie_header, admin_password, session_secret):
                return _html_response(start_response, HTTPStatus.OK, _login_page())
            return _html_response(start_response, HTTPStatus.OK, _editor_page(store.load()))

        return _json_response(start_response, HTTPStatus.NOT_FOUND, {"error": "not_found"})

    return app
