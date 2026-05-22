from __future__ import annotations

import base64
import copy
import json
import mimetypes
import re
from http import HTTPStatus
from pathlib import Path
from typing import Callable, Iterable
from urllib.parse import unquote
from wsgiref.simple_server import make_server

StartResponse = Callable[[str, list[tuple[str, str]]], None]


def _json_response(start_response: StartResponse, status: HTTPStatus, payload: dict | list | None = None):
    body = json.dumps(payload if payload is not None else {}, ensure_ascii=False, indent=2).encode("utf-8")
    start_response(
        f"{status.value} {status.phrase}",
        [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Length", str(len(body))),
            ("Access-Control-Allow-Origin", "*"),
            ("Access-Control-Allow-Methods", "GET, PUT, POST, OPTIONS"),
            ("Access-Control-Allow-Headers", "Content-Type"),
        ],
    )
    return [body]


def _read_json(environ: dict) -> dict:
    length = int(environ.get("CONTENT_LENGTH") or "0")
    raw = environ["wsgi.input"].read(length) if length else b"{}"
    return json.loads(raw.decode("utf-8"))


def _deep_merge(base, patch):
    if isinstance(base, dict) and isinstance(patch, dict):
        merged = copy.deepcopy(base)
        for key, value in patch.items():
            merged[key] = _deep_merge(merged.get(key), value)
        return merged
    return copy.deepcopy(patch)


def _safe_asset_name(filename: str) -> str:
    suffix = Path(filename).suffix.lower() or ".bin"
    stem = Path(filename).stem.lower()
    stem = re.sub(r"[^a-z0-9]+", "-", stem).strip("-") or "asset"
    return f"{stem}{suffix}"


def _content_path(site_dir: Path) -> Path:
    return site_dir / "content" / "site-content.json"


def _load_content(site_dir: Path) -> dict:
    return json.loads(_content_path(site_dir).read_text(encoding="utf-8"))


def _save_content(site_dir: Path, content: dict) -> dict:
    path = _content_path(site_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(content, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return content


def create_app(site_dir: Path | str):
    root = Path(site_dir).resolve()

    def app(environ: dict, start_response: StartResponse) -> Iterable[bytes]:
        method = str(environ.get("REQUEST_METHOD", "GET")).upper()
        raw_path = str(environ.get("PATH_INFO", "/") or "/")
        path = unquote(raw_path)

        if method == "OPTIONS":
            return _json_response(start_response, HTTPStatus.NO_CONTENT, {})

        if path == "/api/content" and method == "GET":
            return _json_response(start_response, HTTPStatus.OK, _load_content(root))

        if path == "/api/content" and method == "PUT":
            current = _load_content(root)
            saved = _save_content(root, _deep_merge(current, _read_json(environ)))
            return _json_response(start_response, HTTPStatus.OK, saved)

        if path == "/api/assets" and method == "POST":
            payload = _read_json(environ)
            try:
                filename = _safe_asset_name(str(payload.get("filename") or "asset.bin"))
                raw = base64.b64decode(str(payload.get("content_base64") or "").encode("ascii"), validate=True)
            except (ValueError, json.JSONDecodeError):
                return _json_response(start_response, HTTPStatus.BAD_REQUEST, {"error": "invalid_asset"})
            target = root / "assets" / "uploads" / filename
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
            return _json_response(start_response, HTTPStatus.OK, {"path": f"./assets/uploads/{filename}"})

        relative = "index.html" if path in {"", "/"} else path.lstrip("/")
        target = (root / relative).resolve()
        try:
            target.relative_to(root)
        except ValueError:
            return _json_response(start_response, HTTPStatus.FORBIDDEN, {"error": "forbidden"})
        if not target.exists() or not target.is_file():
            return _json_response(start_response, HTTPStatus.NOT_FOUND, {"error": "not_found"})
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


def main() -> None:
    site_dir = Path(__file__).resolve().parent
    host = "127.0.0.1"
    port = 8144
    with make_server(host, port, create_app(site_dir)) as server:
        print(f"Hongjuda site running at http://{host}:{port}")
        print(f"Admin running at http://{host}:{port}/admin.html")
        server.serve_forever()


if __name__ == "__main__":
    main()
