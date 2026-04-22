from __future__ import annotations

import json
from urllib.parse import parse_qs
from http import HTTPStatus
from pathlib import Path
from typing import Callable, Iterable

from .auth import COOKIE_NAME, build_session_value, is_authenticated, is_token_authenticated
from .content_store import ContentStore

StartResponse = Callable[[str, list[tuple[str, str]]], None]


EDITOR_SCHEMA = [
    {
        "id": "brand",
        "label": "导航品牌",
        "description": "维护导航栏里的品牌名称与产品副标题。",
        "fields": [
            {"key": "brand_name", "label": "导航品牌名", "type": "text", "placeholder": "Tong Studio"},
            {"key": "brand_tagline", "label": "导航副标题", "type": "text", "placeholder": "Trade Assistant APP"},
        ],
    },
    {
        "id": "hero",
        "label": "首屏工作台",
        "description": "维护首屏主标题、说明和第二屏引导标题。",
        "fields": [
            {"key": "hero_summary_title", "label": "首屏主标题", "type": "textarea", "rows": 3},
            {"key": "hero_intro", "label": "首屏说明", "type": "textarea", "rows": 4},
            {"key": "hero_bridge", "label": "功能区标题", "type": "textarea", "rows": 3},
            {"key": "hero_summary_body", "label": "功能区说明", "type": "textarea", "rows": 4},
        ],
    },
    {
        "id": "pet-ip",
        "label": "产品形象展示",
        "description": "管理 Pet IP 展示区的标题和说明。",
        "fields": [
            {"key": "pet_ip_title", "label": "模块标题", "type": "text"},
            {"key": "pet_ip_body", "label": "模块正文", "type": "textarea", "rows": 5},
        ],
    },
    {
        "id": "trade-assistant",
        "label": "功能卡 1",
        "description": "对应功能扩展区第一张卡片。",
        "fields": [
            {"key": "trade_assistant_title", "label": "模块标题", "type": "text"},
            {"key": "trade_assistant_body", "label": "模块正文", "type": "textarea", "rows": 5},
        ],
    },
    {
        "id": "pet-trade",
        "label": "功能卡 2",
        "description": "对应功能扩展区第二张卡片。",
        "fields": [
            {"key": "pet_trade_title", "label": "模块标题", "type": "text"},
            {"key": "pet_trade_body", "label": "模块正文", "type": "textarea", "rows": 5},
        ],
    },
    {
        "id": "mini-program",
        "label": "功能卡 3",
        "description": "对应功能扩展区第三张卡片。",
        "fields": [
            {"key": "mini_program_title", "label": "模块标题", "type": "text"},
            {"key": "mini_program_body", "label": "模块正文", "type": "textarea", "rows": 5},
        ],
    },
    {
        "id": "contact",
        "label": "收尾转化",
        "description": "管理最后一屏的标题与说明。",
        "fields": [
            {"key": "contact_title", "label": "模块标题", "type": "text"},
            {"key": "contact_body", "label": "模块正文", "type": "textarea", "rows": 5},
        ],
    },
]


IMAGE_SCHEMA = [
    {"key": "home.hero", "label": "首屏主视觉", "description": "首页第一屏的主插画或主图。", "ratio": "4:3"},
    {"key": "home.trade_assistant", "label": "外贸助理配图", "description": "外贸助理模块展示图。", "ratio": "4:3"},
    {"key": "home.pet_trade", "label": "国际贸易配图", "description": "国际贸易模块展示图。", "ratio": "4:3"},
    {"key": "home.mini_program", "label": "小程序开发配图", "description": "小程序模块展示图。", "ratio": "4:3"},
]


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


def _get_bearer_token(environ: dict) -> str | None:
    auth_header = environ.get("HTTP_AUTHORIZATION")
    if not isinstance(auth_header, str):
        return None
    if not auth_header.startswith("Bearer "):
        return None
    return auth_header[7:].strip() or None


def _get_query_token(environ: dict) -> str | None:
    query = environ.get("QUERY_STRING")
    if not isinstance(query, str) or not query:
        return None
    parsed = parse_qs(query, keep_blank_values=False)
    values = parsed.get("token")
    return values[0] if values else None


def _authed(environ: dict, admin_password: str, session_secret: str) -> bool:
    cookie_header = environ.get("COOKIE")
    if is_authenticated(cookie_header if isinstance(cookie_header, str) else None, admin_password, session_secret):
        return True
    token = _get_bearer_token(environ) or _get_query_token(environ)
    return is_token_authenticated(token, admin_password, session_secret)


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
        const submit = event.submitter || document.querySelector('#login-form button[type="submit"]');
        status.textContent = "";
        if (submit) submit.disabled = true;
        status.textContent = "Signing in...";
        const password = document.getElementById("site_admin_password").value;
        try {
          const response = await fetch("/admin/api/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ password }),
          });
          if (!response.ok) {
            status.textContent = "Invalid password.";
            return;
          }
          const payload = await response.json();
          if (payload && payload.token) {
            window.localStorage.setItem("site_admin_token", payload.token);
            status.textContent = "Login successful. Redirecting...";
            window.location.assign(`/admin?token=${encodeURIComponent(payload.token)}`);
            return;
          }
          status.textContent = "Login successful. Redirecting...";
          window.location.assign("/admin");
        } catch (error) {
          status.textContent = "Login failed. Check the local server and try again.";
        } finally {
          if (submit) submit.disabled = false;
        }
      });
    </script>
  </body>
</html>"""


def _editor_page(content: dict, auth_token: str | None = None, admin_meta: dict | None = None) -> str:
    template = """<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Site Content Admin</title>
    <style>
      :root {
        --bg: #edf3fb;
        --panel: rgba(255, 255, 255, 0.84);
        --panel-strong: rgba(255, 255, 255, 0.92);
        --border: rgba(148, 163, 184, 0.24);
        --text: #172033;
        --muted: #61708c;
        --accent: #0f6fff;
        --accent-soft: rgba(15, 111, 255, 0.12);
        --success: #0b8f62;
        --shadow: 0 30px 80px rgba(25, 47, 89, 0.14);
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        min-height: 100vh;
        font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
        color: var(--text);
        background:
          radial-gradient(circle at top left, rgba(132, 213, 255, 0.55), transparent 28%),
          radial-gradient(circle at top right, rgba(223, 196, 255, 0.68), transparent 30%),
          linear-gradient(180deg, #f6f9ff 0%, #edf3fb 100%);
      }
      .admin-shell {
        padding: 28px;
      }
      .admin-frame {
        width: min(1440px, calc(100vw - 56px));
        margin: 0 auto;
        display: grid;
        grid-template-columns: 280px minmax(0, 1fr) 300px;
        gap: 18px;
        align-items: start;
      }
      .glass {
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 28px;
        box-shadow: var(--shadow);
        backdrop-filter: blur(18px);
      }
      .admin-sidebar,
      .admin-content,
      .admin-inspector {
        padding: 22px;
      }
      .brand-mark {
        display: inline-flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 20px;
      }
      .brand-icon {
        width: 42px;
        height: 42px;
        border-radius: 14px;
        display: grid;
        place-items: center;
        background: linear-gradient(135deg, #10b5ff, #8575ff);
        color: #fff;
        font-weight: 700;
        font-size: 18px;
      }
      .brand-copy strong {
        display: block;
        font-size: 18px;
      }
      .brand-copy span {
        color: var(--muted);
        font-size: 13px;
      }
      .section-list {
        display: grid;
        gap: 10px;
        margin-top: 14px;
      }
      .section-button {
        width: 100%;
        border: 1px solid transparent;
        background: rgba(255, 255, 255, 0.68);
        border-radius: 18px;
        padding: 14px 16px;
        text-align: left;
        color: var(--text);
        cursor: pointer;
        transition: transform 140ms ease, border-color 140ms ease, background 140ms ease;
      }
      .section-button:hover {
        transform: translateY(-1px);
        border-color: rgba(15, 111, 255, 0.28);
      }
      .section-button.is-active {
        background: linear-gradient(180deg, rgba(15, 111, 255, 0.14), rgba(15, 111, 255, 0.06));
        border-color: rgba(15, 111, 255, 0.24);
      }
      .section-button strong {
        display: block;
        font-size: 15px;
        margin-bottom: 4px;
      }
      .section-button span {
        color: var(--muted);
        font-size: 12px;
        line-height: 1.55;
      }
      .nav-hint {
        margin-top: 18px;
        padding: 16px;
        border-radius: 18px;
        background: rgba(15, 111, 255, 0.08);
        color: var(--muted);
        font-size: 13px;
        line-height: 1.7;
      }
      .content-header {
        display: flex;
        justify-content: space-between;
        gap: 16px;
        align-items: start;
        margin-bottom: 24px;
      }
      .content-header h1 {
        margin: 0 0 8px;
        font-size: 34px;
      }
      .content-header p {
        margin: 0;
        color: var(--muted);
        line-height: 1.7;
      }
      .lang-switch {
        display: inline-flex;
        padding: 4px;
        gap: 4px;
        background: rgba(15, 23, 42, 0.06);
        border-radius: 999px;
      }
      .lang-button {
        border: 0;
        background: transparent;
        color: var(--muted);
        padding: 10px 16px;
        border-radius: 999px;
        cursor: pointer;
        font-size: 13px;
        font-weight: 700;
      }
      .lang-button.is-active {
        background: #fff;
        color: var(--text);
        box-shadow: 0 8px 20px rgba(25, 47, 89, 0.12);
      }
      .workspace-card {
        background: var(--panel-strong);
        border: 1px solid rgba(255, 255, 255, 0.7);
        border-radius: 24px;
        padding: 22px;
      }
      .workspace-card + .workspace-card {
        margin-top: 16px;
      }
      .workspace-card h2 {
        margin: 0 0 6px;
        font-size: 22px;
      }
      .workspace-card p {
        margin: 0;
        color: var(--muted);
        line-height: 1.7;
      }
      .field-grid {
        display: grid;
        gap: 18px;
        margin-top: 22px;
      }
      .field-grid.two-col {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
      .field-card {
        display: grid;
        gap: 10px;
        padding: 18px;
        border-radius: 20px;
        background: rgba(246, 249, 255, 0.92);
        border: 1px solid rgba(148, 163, 184, 0.18);
      }
      .field-card label {
        font-size: 14px;
        font-weight: 700;
      }
      .field-card small {
        color: var(--muted);
        font-size: 12px;
        line-height: 1.6;
      }
      .field-card input[type="text"],
      .field-card textarea {
        width: 100%;
        border: 1px solid rgba(148, 163, 184, 0.24);
        border-radius: 16px;
        background: #fff;
        padding: 14px 16px;
        color: var(--text);
        font: inherit;
        resize: vertical;
      }
      .field-card input[type="text"]:focus,
      .field-card textarea:focus {
        outline: none;
        border-color: rgba(15, 111, 255, 0.42);
        box-shadow: 0 0 0 4px rgba(15, 111, 255, 0.1);
      }
      .image-grid {
        display: grid;
        gap: 16px;
        margin-top: 20px;
      }
      .image-card {
        display: grid;
        grid-template-columns: 160px minmax(0, 1fr);
        gap: 18px;
        padding: 18px;
        border-radius: 20px;
        background: rgba(246, 249, 255, 0.92);
        border: 1px solid rgba(148, 163, 184, 0.18);
      }
      .image-preview {
        width: 160px;
        height: 120px;
        border-radius: 18px;
        border: 1px solid rgba(148, 163, 184, 0.22);
        overflow: hidden;
        background: linear-gradient(180deg, #f3f7ff, #e7eefb);
        display: grid;
        place-items: center;
      }
      .image-preview img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }
      .image-empty {
        color: var(--muted);
        font-size: 13px;
      }
      .image-meta h3 {
        margin: 0 0 6px;
        font-size: 17px;
      }
      .image-meta p {
        margin: 0 0 14px;
        color: var(--muted);
        line-height: 1.7;
      }
      .image-tools {
        display: grid;
        gap: 10px;
      }
      .image-tools input[type="text"] {
        width: 100%;
        border: 1px solid rgba(148, 163, 184, 0.24);
        border-radius: 14px;
        padding: 12px 14px;
        font: inherit;
        background: #fff;
      }
      .image-actions {
        display: flex;
        gap: 10px;
        align-items: center;
        flex-wrap: wrap;
      }
      .button,
      .ghost-button {
        border: 0;
        border-radius: 16px;
        padding: 12px 16px;
        font: inherit;
        cursor: pointer;
        transition: transform 140ms ease, opacity 140ms ease;
      }
      .button:hover,
      .ghost-button:hover {
        transform: translateY(-1px);
      }
      .button {
        background: linear-gradient(135deg, #11203b, #1f2f57);
        color: #fff;
      }
      .ghost-button {
        background: rgba(15, 23, 42, 0.06);
        color: var(--text);
      }
      .upload-name {
        color: var(--muted);
        font-size: 12px;
      }
      .stats {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 12px;
        margin-top: 18px;
      }
      .stat-card {
        padding: 16px;
        border-radius: 18px;
        background: rgba(246, 249, 255, 0.92);
        border: 1px solid rgba(148, 163, 184, 0.18);
      }
      .stat-card strong {
        display: block;
        font-size: 24px;
        margin-top: 8px;
      }
      .stat-card span {
        color: var(--muted);
        font-size: 12px;
      }
      .inspector-title {
        margin: 0 0 10px;
        font-size: 20px;
      }
      .inspector-copy {
        margin: 0 0 18px;
        color: var(--muted);
        line-height: 1.7;
      }
        .action-stack {
          display: grid;
          gap: 12px;
        }
      .inspector-actions {
        display: grid;
        gap: 10px;
      }
      .status-chip {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 12px;
        border-radius: 999px;
        background: rgba(11, 143, 98, 0.12);
        color: var(--success);
        font-size: 12px;
        font-weight: 700;
      }
      .status-chip.is-draft {
        background: rgba(15, 111, 255, 0.12);
        color: var(--accent);
      }
      .status-chip.is-risk {
        background: rgba(180, 35, 24, 0.12);
        color: #b42318;
      }
      .status-chip.is-dirty {
        background: rgba(245, 158, 11, 0.14);
        color: #b45309;
      }
      .status-chip::before {
        content: "";
        width: 8px;
        height: 8px;
        border-radius: 999px;
        background: currentColor;
      }
      .inspector-panel {
        padding: 18px;
        border-radius: 20px;
        background: rgba(246, 249, 255, 0.92);
        border: 1px solid rgba(148, 163, 184, 0.18);
      }
      .inspector-panel h3 {
        margin: 0 0 8px;
        font-size: 16px;
      }
      .inspector-panel p,
      .inspector-panel li,
      .inspector-panel dt,
      .inspector-panel dd {
        margin: 0;
        color: var(--muted);
        font-size: 13px;
        line-height: 1.7;
      }
      .inspector-panel dl {
        display: grid;
        gap: 10px;
        margin: 0;
      }
      .inspector-panel dt {
        font-weight: 700;
        color: var(--text);
      }
      .inspector-panel dd + dt {
        margin-top: 8px;
      }
      .inspector-panel ul {
        margin: 10px 0 0;
        padding-left: 18px;
      }
      .history-list {
        display: grid;
        gap: 10px;
      }
      .history-item {
        padding: 12px 14px;
        border-radius: 16px;
        background: rgba(255, 255, 255, 0.74);
        border: 1px solid rgba(148, 163, 184, 0.16);
      }
      .history-item strong {
        display: block;
        font-size: 13px;
        margin-bottom: 4px;
      }
      .warning-list {
        display: grid;
        gap: 10px;
      }
      .warning-item {
        padding: 12px 14px;
        border-radius: 16px;
        background: rgba(245, 158, 11, 0.10);
        border: 1px solid rgba(245, 158, 11, 0.18);
        color: #9a6700;
        font-size: 13px;
        line-height: 1.65;
      }
      .warning-item strong {
        display: block;
        color: #7c5300;
        margin-bottom: 4px;
      }
      .diff-list {
        display: grid;
        gap: 10px;
      }
      .diff-item {
        padding: 12px 14px;
        border-radius: 16px;
        background: rgba(15, 111, 255, 0.08);
        border: 1px solid rgba(15, 111, 255, 0.14);
        color: #18437b;
        font-size: 13px;
        line-height: 1.7;
      }
      .diff-item strong {
        display: block;
        margin-bottom: 4px;
        color: #102f57;
      }
      .preview-state {
        display: grid;
        gap: 14px;
      }
      .preview-summary {
        display: grid;
        gap: 10px;
      }
      .preview-summary strong {
        font-size: 15px;
      }
      .preview-summary span {
        color: var(--muted);
        font-size: 13px;
        line-height: 1.7;
      }
      .preview-metrics {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 10px;
      }
      .preview-metric {
        padding: 12px 14px;
        border-radius: 16px;
        background: rgba(255, 255, 255, 0.72);
        border: 1px solid rgba(148, 163, 184, 0.18);
      }
      .preview-metric span {
        display: block;
        color: var(--muted);
        font-size: 12px;
        margin-bottom: 6px;
      }
      .preview-metric strong {
        font-size: 22px;
      }
      .preview-assets {
        display: grid;
        gap: 10px;
      }
      .preview-asset {
        padding: 12px 14px;
        border-radius: 16px;
        background: rgba(255, 255, 255, 0.72);
        border: 1px solid rgba(148, 163, 184, 0.18);
      }
      .preview-asset strong {
        display: block;
        font-size: 13px;
        margin-bottom: 6px;
      }
      .preview-asset span {
        display: block;
        color: var(--muted);
        font-size: 12px;
        line-height: 1.6;
        word-break: break-all;
      }
      .preview-asset.ok {
        border-color: rgba(11, 143, 98, 0.22);
      }
      .preview-asset.risk {
        border-color: rgba(180, 35, 24, 0.22);
        background: rgba(255, 244, 243, 0.92);
      }
      .preview-asset em {
        display: inline-flex;
        margin-top: 8px;
        font-style: normal;
        font-size: 12px;
        font-weight: 700;
      }
      .preview-asset.ok em {
        color: var(--success);
      }
      .preview-asset.risk em {
        color: #b42318;
      }
      .ok-note {
        color: var(--success);
        font-size: 13px;
        line-height: 1.7;
      }
      .field-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
      }
      .field-counter {
        padding: 5px 10px;
        border-radius: 999px;
        background: rgba(15, 23, 42, 0.06);
        color: var(--muted);
        font-size: 12px;
        font-weight: 700;
        white-space: nowrap;
      }
      .field-counter.is-over {
        background: rgba(245, 158, 11, 0.14);
        color: #9a6700;
      }
      .modal {
        position: fixed;
        inset: 0;
        display: none;
        align-items: center;
        justify-content: center;
        padding: 24px;
        background: rgba(10, 18, 34, 0.38);
        backdrop-filter: blur(8px);
        z-index: 20;
      }
      .modal.is-open {
        display: flex;
      }
      .modal-card {
        width: min(520px, 100%);
        padding: 24px;
        border-radius: 26px;
        background: rgba(255, 255, 255, 0.96);
        border: 1px solid rgba(148, 163, 184, 0.18);
        box-shadow: 0 30px 80px rgba(20, 32, 58, 0.18);
      }
      .modal-card h3 {
        margin: 0 0 10px;
        font-size: 24px;
      }
      .modal-card p {
        margin: 0;
        color: var(--muted);
        line-height: 1.7;
      }
      .modal-actions {
        display: flex;
        justify-content: flex-end;
        gap: 10px;
        margin-top: 20px;
      }
      #save-status {
        min-height: 24px;
        font-size: 13px;
        color: var(--muted);
      }
      @media (max-width: 1200px) {
        .admin-frame {
          grid-template-columns: 1fr;
        }
      }
      @media (max-width: 760px) {
        .admin-shell {
          padding: 16px;
        }
        .admin-frame {
          width: 100%;
        }
        .content-header {
          flex-direction: column;
        }
        .field-grid.two-col,
        .stats {
          grid-template-columns: 1fr;
        }
        .image-card {
          grid-template-columns: 1fr;
        }
        .image-preview {
          width: 100%;
          height: 180px;
        }
      }
    </style>
  </head>
  <body>
    <main class="admin-shell">
      <div class="admin-frame">
        <aside class="admin-sidebar glass">
          <div class="brand-mark">
            <div class="brand-icon">TS</div>
            <div class="brand-copy">
              <strong>内容管理台</strong>
              <span>CMS-style editor for Tongxi Fairy Lab</span>
            </div>
          </div>
          <div id="content-navigator" class="section-list"></div>
          <div class="nav-hint">
            左侧选择区块，右侧只显示该区块的可编辑字段和素材信息。后台人员不需要直接处理 JSON。
          </div>
        </aside>

        <section class="admin-content glass">
          <div class="content-header">
            <div>
              <h1>Site Content Admin</h1>
              <p>当前使用区块化 CMS 编辑模式，适合运营或内容管理人员直接维护首页文案与图片资源。</p>
            </div>
            <div class="lang-switch" id="lang-switch">
              <button class="lang-button is-active" type="button" data-lang="zh">中文内容</button>
              <button class="lang-button" type="button" data-lang="en">English Content</button>
            </div>
          </div>
          <div id="workspace"></div>
        </section>

        <aside class="admin-inspector glass">
          <h2 class="inspector-title">发布侧栏</h2>
          <p class="inspector-copy">这里用于查看当前编辑状态、执行保存、恢复最近内容，以及确认图片是否已替换。</p>
          <div class="action-stack">
            <span id="dirty-chip" class="status-chip">已同步</span>
            <div class="inspector-actions">
              <button id="preview-home" type="button" class="ghost-button">预览首页</button>
              <button id="preflight-check" type="button" class="ghost-button">发布前检查</button>
              <button id="save-content" type="button" class="button">保存当前改动</button>
              <button id="publish-content" type="button" class="button">正式发布</button>
              <button id="reset-content" type="button" class="ghost-button">恢复最近保存版本</button>
            </div>
            <div id="save-status">当前没有未保存改动。</div>
          </div>
          <div class="stats" id="inspector-stats"></div>
          <div class="inspector-panel">
            <h3>当前区块提示</h3>
            <p id="section-description">选择左侧区块开始编辑。</p>
          </div>
          <div class="inspector-panel">
            <h3>发布记录 / 最近修改时间</h3>
            <dl>
              <dt>最近修改时间</dt>
              <dd id="last-updated">尚未保存内容</dd>
            </dl>
            <div id="publish-history" class="history-list" style="margin-top: 14px;"></div>
          </div>
          <div class="inspector-panel">
            <h3>发布前检查</h3>
            <div id="warning-list" class="warning-list"></div>
            <p id="warning-ok" class="ok-note" hidden>当前内容没有发现明显的发布风险。</p>
          </div>
          <div class="inspector-panel">
            <h3>首页预览差异提示</h3>
            <div id="preview-diff" class="diff-list"></div>
            <p id="preview-diff-ok" class="ok-note" hidden>当前草稿与最近保存版本一致，直接预览即可。</p>
          </div>
          <div class="inspector-panel">
            <h3>预览状态</h3>
            <div id="preview-state" class="preview-state"></div>
          </div>
          <div class="inspector-panel">
            <h3>运营建议</h3>
            <ul>
              <li>中文和英文内容分开维护，避免互相覆盖。</li>
              <li>替换图片后建议回首页检查实际展示比例。</li>
              <li>每次集中改一个区块，能减少误改风险。</li>
            </ul>
          </div>
        </aside>
      </div>
    </main>
    <div id="publish-modal" class="modal" aria-hidden="true">
      <div class="modal-card">
        <h3>确认正式发布</h3>
        <p>正式发布会记录一条发布时间，适合在你确认首页内容与预览结果一致后执行。这个动作不会自动部署外部环境，但会留下后台发布记录。</p>
        <div class="modal-actions">
          <button id="cancel-publish" type="button" class="ghost-button">取消</button>
          <button id="confirm-publish" type="button" class="button">确认发布</button>
        </div>
      </div>
    </div>
    <div id="preview-modal" class="modal" aria-hidden="true">
      <div class="modal-card">
        <h3>确认预览首页</h3>
        <p id="preview-modal-copy">当前预览将带上草稿变更，仅用于查看前台效果，不会覆盖正式内容。</p>
        <div id="preview-modal-list" class="warning-list" style="margin-top: 14px;"></div>
        <div class="modal-actions">
          <button id="cancel-preview" type="button" class="ghost-button">取消</button>
          <button id="confirm-preview" type="button" class="button">继续预览</button>
        </div>
      </div>
    </div>
    <script>
      const initialContent = __CONTENT_JSON__;
      const editorSchema = __EDITOR_SCHEMA__;
      const imageSchema = __IMAGE_SCHEMA__;
      const initialMeta = __META_JSON__;
      const adminToken = __TOKEN_JSON__ || window.localStorage.getItem("site_admin_token") || "";

      const sections = [...editorSchema, {
        id: "images",
        label: "图片资源",
        description: "管理首页区块图片、路径与素材替换。",
        fields: [],
      }];

      let currentSectionId = sections[0].id;
      let currentLang = "zh";
      let savedContent = JSON.parse(JSON.stringify(initialContent));
      let workingContent = JSON.parse(JSON.stringify(initialContent));
      let adminMeta = initialMeta || { updated_at: null, history: [] };
      let dirty = false;
      let previewDiagnostics = { checking: false, checkedAt: null, assetChecks: [] };
      let previewValidationTimer = null;

      function ensureShape() {
        if (!workingContent.strings) workingContent.strings = {};
        if (!workingContent.strings.zh) workingContent.strings.zh = {};
        if (!workingContent.strings.en) workingContent.strings.en = {};
        if (!workingContent.images) workingContent.images = {};
      }

      ensureShape();

      function buildHeaders() {
        const headers = { "Content-Type": "application/json" };
        if (adminToken) headers.Authorization = `Bearer ${adminToken}`;
        return headers;
      }

      function setDirty(nextDirty, message) {
        dirty = nextDirty;
        const chip = document.getElementById("dirty-chip");
        const status = document.getElementById("save-status");
        chip.classList.toggle("is-dirty", dirty);
        chip.textContent = dirty ? "有未保存改动" : "已同步";
        if (message) status.textContent = message;
      }

      function updateStats() {
        const textCount = editorSchema.reduce((count, section) => count + section.fields.length, 0);
        const currentSection = sections.find((item) => item.id === currentSectionId);
        document.getElementById("inspector-stats").innerHTML = `
          <div class="stat-card">
            <span>已配置区块</span>
            <strong>${sections.length}</strong>
          </div>
          <div class="stat-card">
            <span>文案字段</span>
            <strong>${textCount}</strong>
          </div>
          <div class="stat-card">
            <span>图片槽位</span>
            <strong>${imageSchema.length}</strong>
          </div>
          <div class="stat-card">
            <span>当前区块</span>
            <strong>${currentSection ? currentSection.label : "-"}</strong>
          </div>
        `;
      }

      function formatTime(value) {
        if (!value) return "尚未保存内容";
        const parsed = new Date(value);
        if (Number.isNaN(parsed.getTime())) return value;
        return parsed.toLocaleString("zh-CN", {
          year: "numeric",
          month: "2-digit",
          day: "2-digit",
          hour: "2-digit",
          minute: "2-digit",
        });
      }

      function measureLength(text) {
        return (text || "").replace(/\\s+/g, "").length;
      }

      function recommendLength(key) {
        if (key.includes("title")) return 26;
        if (key.includes("intro") || key.includes("bridge")) return 90;
        return 120;
      }

      function fieldHint(field) {
        const limit = recommendLength(field.key);
        return `建议 ${currentLang === "zh" ? "中文" : "英文"} 控制在 ${limit} 字以内`;
      }

      function collectWarnings() {
        const warnings = [];
        for (const lang of ["zh", "en"]) {
          for (const section of editorSchema) {
            for (const field of section.fields) {
              const value = workingContent.strings?.[lang]?.[field.key] || "";
              const currentLength = measureLength(value);
              const limit = recommendLength(field.key);
              if (currentLength > limit) {
                warnings.push({
                  title: `${section.label} / ${field.label}`,
                  detail: `${lang === "zh" ? "中文" : "英文"} 当前约 ${currentLength} 字，建议控制在 ${limit} 字以内，避免首页排版过满。`,
                });
              }
            }
          }
        }
        imageSchema.forEach((image) => {
          const path = workingContent.images?.[image.key] || "";
          if (!path) {
            warnings.push({
              title: `${image.label}`,
              detail: "当前未设置图片路径，发布后该区块可能失去视觉锚点。",
            });
          }
        });
        (previewDiagnostics.assetChecks || []).filter((item) => !item.ok).forEach((item) => {
          warnings.push({
            title: item.label,
            detail: item.detail || "当前图片在预览中可能无法正常加载。",
          });
        });
        return warnings;
      }

      function collectDiffs() {
        const diffs = [];
        for (const lang of ["zh", "en"]) {
          for (const section of editorSchema) {
            for (const field of section.fields) {
              const before = savedContent.strings?.[lang]?.[field.key] || "";
              const after = workingContent.strings?.[lang]?.[field.key] || "";
              if (before !== after) {
                diffs.push({
                  title: `${section.label} / ${field.label}`,
                  detail: `${lang === "zh" ? "中文" : "英文"} 已修改，预览首页时会显示草稿内容。`,
                });
              }
            }
          }
        }
        imageSchema.forEach((image) => {
          const before = savedContent.images?.[image.key] || "";
          const after = workingContent.images?.[image.key] || "";
          if (before !== after) {
            diffs.push({
              title: image.label,
              detail: "图片资源已变更，预览首页会优先展示草稿图片路径。",
            });
          }
        });
        return diffs;
      }

      function renderWarnings() {
        const warnings = collectWarnings();
        const warningList = document.getElementById("warning-list");
        const okNote = document.getElementById("warning-ok");
        if (!warnings.length) {
          warningList.innerHTML = "";
          okNote.hidden = false;
          return;
        }
        okNote.hidden = true;
        warningList.innerHTML = warnings.map((warning) => `
          <div class="warning-item">
            <strong>${warning.title}</strong>
            <span>${warning.detail}</span>
          </div>
        `).join("");
      }

      function renderDiffs() {
        const diffs = collectDiffs();
        const diffRoot = document.getElementById("preview-diff");
        const okNote = document.getElementById("preview-diff-ok");
        if (!diffs.length) {
          diffRoot.innerHTML = "";
          okNote.hidden = false;
          return;
        }
        okNote.hidden = true;
        diffRoot.innerHTML = diffs.map((diff) => `
          <div class="diff-item">
            <strong>${diff.title}</strong>
            <span>${diff.detail}</span>
          </div>
        `).join("");
      }

      function renderMeta() {
        document.getElementById("last-updated").textContent = formatTime(adminMeta.updated_at);
        const historyRoot = document.getElementById("publish-history");
        const history = Array.isArray(adminMeta.history) ? adminMeta.history : [];
        if (!history.length) {
          historyRoot.innerHTML = `<div class="history-item"><strong>暂无记录</strong><span>首次保存后会在这里留下最近修改时间。</span></div>`;
          return;
        }
        historyRoot.innerHTML = history.map((item) => `
          <div class="history-item">
            <strong>${item.label || "内容已保存"}</strong>
            <span>${formatTime(item.timestamp)}</span>
          </div>
        `).join("");
      }

      function getDiffStats() {
        let textChanges = 0;
        let imageChanges = 0;
        for (const lang of ["zh", "en"]) {
          for (const section of editorSchema) {
            for (const field of section.fields) {
              const before = savedContent.strings?.[lang]?.[field.key] || "";
              const after = workingContent.strings?.[lang]?.[field.key] || "";
              if (before !== after) textChanges += 1;
            }
          }
        }
        imageSchema.forEach((image) => {
          const before = savedContent.images?.[image.key] || "";
          const after = workingContent.images?.[image.key] || "";
          if (before !== after) imageChanges += 1;
        });
        return { textChanges, imageChanges, totalChanges: textChanges + imageChanges };
      }

      function normalizeAssetPath(path) {
        if (!path) return "";
        if (path.startsWith("http://") || path.startsWith("https://") || path.startsWith("data:")) return path;
        if (path.startsWith("./")) return `/${path.slice(2)}`;
        if (path.startsWith("/")) return path;
        return `/${path}`;
      }

      async function validateImageAssets() {
        previewDiagnostics = { ...previewDiagnostics, checking: true };
        renderPreviewStatus();
        const assetChecks = await Promise.all(imageSchema.map(async (image) => {
          const path = workingContent.images?.[image.key] || "";
          if (!path) {
            return { key: image.key, label: image.label, path, ok: false, detail: "当前未设置图片路径。" };
          }
          try {
            const response = await fetch(normalizeAssetPath(path), { method: "GET", cache: "no-store" });
            return {
              key: image.key,
              label: image.label,
              path,
              ok: response.ok,
              detail: response.ok ? "预览时可正常加载。" : `预览加载失败（HTTP ${response.status}）。`,
            };
          } catch (error) {
            return { key: image.key, label: image.label, path, ok: false, detail: "预览时无法读取这张图片。" };
          }
        }));
        previewDiagnostics = { checking: false, checkedAt: new Date().toISOString(), assetChecks };
        renderPreviewStatus();
        return assetChecks;
      }

      function queuePreviewAssetValidation(immediate = false) {
        if (previewValidationTimer) window.clearTimeout(previewValidationTimer);
        if (immediate) return validateImageAssets();
        previewDiagnostics = { ...previewDiagnostics, checking: true };
        renderPreviewStatus();
        previewValidationTimer = window.setTimeout(() => {
          validateImageAssets();
        }, 180);
        return Promise.resolve(previewDiagnostics.assetChecks || []);
      }

      function renderPreviewStatus() {
        const root = document.getElementById("preview-state");
        const stats = getDiffStats();
        const failedAssets = (previewDiagnostics.assetChecks || []).filter((item) => !item.ok);
        const modeClass = failedAssets.length ? "status-chip is-risk" : stats.totalChanges ? "status-chip is-draft" : "status-chip";
        const modeLabel = failedAssets.length ? "预览有素材风险" : stats.totalChanges ? "将以草稿预览" : "直接预览正式内容";
        const summary = failedAssets.length
          ? "检测到图片素材可能在预览里失效，建议先处理再打开首页预览。"
          : stats.totalChanges
            ? "当前预览会带上未保存草稿，但不会覆盖正式内容。"
            : "当前没有草稿差异，预览结果会与已保存内容一致。";
        const checkedAt = previewDiagnostics.checkedAt ? `上次检查：${formatTime(previewDiagnostics.checkedAt)}` : "尚未完成预览素材检查。";
        const assets = (previewDiagnostics.assetChecks || []).length
          ? previewDiagnostics.assetChecks.map((item) => `
            <div class="preview-asset ${item.ok ? "ok" : "risk"}">
              <strong>${item.label}</strong>
              <span>${item.path || "未设置路径"}</span>
              <em>${item.detail}</em>
            </div>
          `).join("")
          : `<div class="preview-asset"><strong>图片素材检查</strong><span>${previewDiagnostics.checking ? "正在检查..." : "还没有最新的预览检查结果。"}</span></div>`;
        root.innerHTML = `
          <div class="preview-summary">
            <span class="${modeClass}">${modeLabel}</span>
            <strong>预览内容和正式内容的关系已明确标注</strong>
            <span>${summary}</span>
            <span>${previewDiagnostics.checking ? "正在更新预览素材状态..." : checkedAt}</span>
          </div>
          <div class="preview-metrics">
            <div class="preview-metric">
              <span>文案变更</span>
              <strong>${stats.textChanges}</strong>
            </div>
            <div class="preview-metric">
              <span>图片变更</span>
              <strong>${stats.imageChanges}</strong>
            </div>
          </div>
          <div class="preview-assets">${assets}</div>
        `;
      }

      function launchPreviewWindow() {
        const diffs = collectDiffs();
        window.localStorage.setItem("site_content_preview", JSON.stringify(workingContent));
        if (diffs.length) {
          setDirty(dirty, `预览首页将带上 ${diffs.length} 处草稿变更。`);
        }
        window.open("/?preview=1", "_blank");
      }

      function openPreviewModal(summary, items) {
        document.getElementById("preview-modal-copy").textContent = summary;
        document.getElementById("preview-modal-list").innerHTML = items.map((item) => `
          <div class="warning-item">
            <strong>${item.title}</strong>
            <span>${item.detail}</span>
          </div>
        `).join("");
        const modal = document.getElementById("preview-modal");
        modal.classList.add("is-open");
        modal.setAttribute("aria-hidden", "false");
      }

      function closePreviewModal() {
        const modal = document.getElementById("preview-modal");
        modal.classList.remove("is-open");
        modal.setAttribute("aria-hidden", "true");
      }

      function renderNav() {
        const nav = document.getElementById("content-navigator");
        nav.innerHTML = sections.map((section) => `
          <button class="section-button ${section.id === currentSectionId ? "is-active" : ""}" type="button" data-section="${section.id}">
            <strong>${section.label}</strong>
            <span>${section.description}</span>
          </button>
        `).join("");
      }

      function renderLangSwitch() {
        document.querySelectorAll(".lang-button").forEach((button) => {
          button.classList.toggle("is-active", button.dataset.lang === currentLang);
        });
      }

      function renderTextSection(section) {
        const fields = section.fields.map((field) => {
          const value = workingContent.strings[currentLang][field.key] || "";
          const placeholder = field.placeholder || "";
          const limit = recommendLength(field.key);
          const currentLength = measureLength(value);
          const counterClass = currentLength > limit ? "field-counter is-over" : "field-counter";
          if (field.type === "textarea") {
            return `
              <div class="field-card">
                <div class="field-head">
                  <label for="${field.key}">${field.label}</label>
                  <span class="${counterClass}">${currentLength}/${limit}</span>
                </div>
                <small>${fieldHint(field)}</small>
                <textarea id="${field.key}" rows="${field.rows || 4}" data-field="${field.key}" placeholder="${placeholder}">${value}</textarea>
              </div>
            `;
          }
          return `
            <div class="field-card">
              <div class="field-head">
                <label for="${field.key}">${field.label}</label>
                <span class="${counterClass}">${currentLength}/${limit}</span>
              </div>
              <small>${fieldHint(field)}</small>
              <input id="${field.key}" type="text" data-field="${field.key}" value="${value.replace(/"/g, "&quot;")}" placeholder="${placeholder}">
            </div>
          `;
        }).join("");

        return `
          <div class="workspace-card">
            <h2>${section.label}</h2>
            <p>${section.description}</p>
            <div class="field-grid ${section.fields.length > 2 ? "two-col" : ""}">
              ${fields}
            </div>
          </div>
        `;
      }

      function renderImageSection() {
        const cards = imageSchema.map((image) => {
          const path = workingContent.images[image.key] || "";
          const preview = path ? `<img src="${path}" alt="${image.label}">` : `<div class="image-empty">暂无图片</div>`;
          return `
            <div class="image-card">
              <div class="image-preview">${preview}</div>
              <div class="image-meta">
                <h3>${image.label}</h3>
                <p>${image.description} 建议比例：${image.ratio || "4:3"}。</p>
                <div class="image-tools">
                  <input type="text" data-image-field="${image.key}" value="${path.replace(/"/g, "&quot;")}" placeholder="./assets/example.png">
                  <div class="image-actions">
                    <input type="file" id="file-${image.key}" data-image-upload="${image.key}" accept="image/*" hidden>
                    <button type="button" class="button" data-upload-trigger="${image.key}">上传新图片</button>
                    <button type="button" class="ghost-button" data-clear-image="${image.key}">清空图片</button>
                    <span class="upload-name" id="label-${image.key}">${path || "当前未设置图片路径"}</span>
                  </div>
                </div>
              </div>
            </div>
          `;
        }).join("");

        return `
          <div class="workspace-card">
            <h2>图片资源管理</h2>
            <p>每张图片可以直接改路径，也可以从这里上传新素材并自动回填路径。</p>
            <div class="image-grid">${cards}</div>
          </div>
        `;
      }

      function renderWorkspace() {
        const currentSection = sections.find((item) => item.id === currentSectionId);
        document.getElementById("section-description").textContent = currentSection ? currentSection.description : "";
        const workspace = document.getElementById("workspace");
        if (!currentSection || currentSection.id === "images") {
          workspace.innerHTML = renderImageSection();
          return;
        }
        workspace.innerHTML = renderTextSection(currentSection);
      }

      function renderAll() {
        renderNav();
        renderLangSwitch();
        renderWorkspace();
        updateStats();
        renderWarnings();
        renderDiffs();
        renderMeta();
        renderPreviewStatus();
      }

      function updateTextField(key, value) {
        workingContent.strings[currentLang][key] = value;
        setDirty(true, "检测到文案修改，记得保存。");
      }

      function updateImageField(key, value) {
        workingContent.images[key] = value;
        setDirty(true, "图片路径已更新，保存后前台才会读取到新内容。");
        renderWorkspace();
        queuePreviewAssetValidation();
      }

      async function uploadImage(key, file) {
        const status = document.getElementById("save-status");
        status.textContent = "正在上传图片...";
        const buffer = await file.arrayBuffer();
        let binary = "";
        const bytes = new Uint8Array(buffer);
        bytes.forEach((value) => { binary += String.fromCharCode(value); });
        const response = await fetch("/admin/api/assets", {
          method: "POST",
          headers: buildHeaders(),
          body: JSON.stringify({
            filename: file.name,
            content_base64: btoa(binary),
          }),
        });
        if (!response.ok) {
          status.textContent = "图片上传失败，请重试。";
          return;
        }
        const payload = await response.json();
        workingContent.images[key] = payload.path;
        setDirty(true, `图片已上传：${payload.path}`);
        renderWorkspace();
        queuePreviewAssetValidation();
      }

      async function saveContent() {
        const status = document.getElementById("save-status");
        status.textContent = "正在保存内容...";
        const response = await fetch("/admin/api/content", {
          method: "PUT",
          headers: buildHeaders(),
          body: JSON.stringify(workingContent),
        });
        if (!response.ok) {
          status.textContent = "保存失败，请检查登录状态后重试。";
          return;
        }
        const saved = await response.json();
        savedContent = JSON.parse(JSON.stringify(saved));
        workingContent = JSON.parse(JSON.stringify(saved));
        ensureShape();
        await refreshMeta();
        setDirty(false, "已保存到内容文件。");
        renderAll();
        await queuePreviewAssetValidation(true);
      }

      async function refreshMeta() {
        const response = await fetch("/admin/api/meta", {
          method: "GET",
          headers: buildHeaders(),
        });
        if (!response.ok) return;
        adminMeta = await response.json();
      }

      async function previewHome() {
        const assetChecks = await queuePreviewAssetValidation(true);
        renderWarnings();
        const stats = getDiffStats();
        const failedAssets = (assetChecks || []).filter((item) => !item.ok);
        const items = [];
        if (stats.textChanges || stats.imageChanges) {
          items.push({
            title: "草稿预览",
            detail: `这次预览将带上 ${stats.textChanges} 处文案变更和 ${stats.imageChanges} 处图片变更，不会覆盖正式首页。`,
          });
        }
        failedAssets.forEach((item) => {
          items.push({
            title: item.label,
            detail: item.detail || "当前图片在预览中可能无法正常加载。",
          });
        });
        if (items.length) {
          openPreviewModal(
            failedAssets.length
              ? "预览前检查到图片素材风险，你仍可以继续打开预览，但建议先处理这些问题。"
              : "当前预览会使用草稿内容，仅用于查看前台效果，不会发布到正式页面。",
            items,
          );
          return;
        }
        launchPreviewWindow();
      }

      async function runPreflightCheck() {
        await queuePreviewAssetValidation(true);
        renderWarnings();
        const warnings = collectWarnings();
        if (!warnings.length) {
          setDirty(dirty, "发布前检查通过，可以先预览首页再发布。");
          return;
        }
        setDirty(dirty, `发布前检查发现 ${warnings.length} 项需要关注的问题。`);
      }

      async function publishContent() {
        const status = document.getElementById("save-status");
        status.textContent = "正在记录正式发布时间...";
        const response = await fetch("/admin/api/publish", {
          method: "POST",
          headers: buildHeaders(),
          body: JSON.stringify({}),
        });
        if (!response.ok) {
          status.textContent = "正式发布记录失败，请先确认保存状态。";
          return;
        }
        adminMeta = await response.json();
        closePublishModal();
        setDirty(false, "已记录正式发布时间。");
        renderMeta();
      }

      function openPublishModal() {
        const warnings = collectWarnings();
        if (warnings.length) {
          setDirty(dirty, `正式发布前还有 ${warnings.length} 项风险，建议先处理。`);
        }
        const modal = document.getElementById("publish-modal");
        modal.classList.add("is-open");
        modal.setAttribute("aria-hidden", "false");
      }

      function closePublishModal() {
        const modal = document.getElementById("publish-modal");
        modal.classList.remove("is-open");
        modal.setAttribute("aria-hidden", "true");
      }

      function resetContent() {
        workingContent = JSON.parse(JSON.stringify(savedContent));
        ensureShape();
        setDirty(false, "已恢复到最近保存版本。");
        renderAll();
        queuePreviewAssetValidation();
      }

      document.addEventListener("click", (event) => {
        const sectionButton = event.target.closest("[data-section]");
        if (sectionButton) {
          currentSectionId = sectionButton.dataset.section;
          renderAll();
          return;
        }

        const langButton = event.target.closest("[data-lang]");
        if (langButton) {
          currentLang = langButton.dataset.lang;
          renderAll();
          return;
        }

        const uploadTrigger = event.target.closest("[data-upload-trigger]");
        if (uploadTrigger) {
          const key = uploadTrigger.dataset.uploadTrigger;
          const input = document.getElementById(`file-${key}`);
          if (input) input.click();
          return;
        }

        const clearImage = event.target.closest("[data-clear-image]");
        if (clearImage) {
          workingContent.images[clearImage.dataset.clearImage] = "";
          setDirty(true, "图片已清空，保存后生效。");
          renderWorkspace();
          queuePreviewAssetValidation();
        }
      });

      document.addEventListener("input", (event) => {
        const field = event.target.closest("[data-field]");
        if (field) {
          updateTextField(field.dataset.field, field.value);
          return;
        }
        const imageField = event.target.closest("[data-image-field]");
        if (imageField) {
          updateImageField(imageField.dataset.imageField, imageField.value);
        }
      });

      document.addEventListener("change", (event) => {
        const fileInput = event.target.closest("[data-image-upload]");
        if (fileInput && fileInput.files && fileInput.files[0]) {
          uploadImage(fileInput.dataset.imageUpload, fileInput.files[0]);
        }
      });

      document.getElementById("save-content").addEventListener("click", saveContent);
      document.getElementById("reset-content").addEventListener("click", resetContent);
      document.getElementById("preview-home").addEventListener("click", previewHome);
      document.getElementById("preflight-check").addEventListener("click", runPreflightCheck);
      document.getElementById("publish-content").addEventListener("click", openPublishModal);
      document.getElementById("cancel-publish").addEventListener("click", closePublishModal);
      document.getElementById("confirm-publish").addEventListener("click", publishContent);
      document.getElementById("cancel-preview").addEventListener("click", closePreviewModal);
      document.getElementById("confirm-preview").addEventListener("click", () => {
        closePreviewModal();
        launchPreviewWindow();
      });

      renderAll();
      queuePreviewAssetValidation(true);
    </script>
  </body>
</html>"""
    return (
        template
        .replace("__CONTENT_JSON__", json.dumps(content, ensure_ascii=False))
        .replace("__EDITOR_SCHEMA__", json.dumps(EDITOR_SCHEMA, ensure_ascii=False))
        .replace("__IMAGE_SCHEMA__", json.dumps(IMAGE_SCHEMA, ensure_ascii=False))
        .replace("__META_JSON__", json.dumps(admin_meta or {"updated_at": None, "history": []}, ensure_ascii=False))
        .replace("__TOKEN_JSON__", json.dumps(auth_token or "", ensure_ascii=False))
    )


def create_app(
    root_dir: Path,
    admin_password: str,
    session_secret: str,
    site_dir: Path | None = None,
    default_content: dict | None = None,
    source_html_path: Path | None = None,
    extract_callback=None,
    sync_callback=None,
):
    resolved_site_dir = site_dir or (root_dir / "website_from_playground")
    store = ContentStore(
        resolved_site_dir,
        default_content=default_content,
        source_html_path=source_html_path,
        extract_callback=extract_callback,
        sync_callback=sync_callback,
    )

    def app(environ: dict, start_response: StartResponse) -> Iterable[bytes]:
        method = str(environ.get("REQUEST_METHOD", "GET")).upper()
        path = str(environ.get("PATH_INFO", "/"))

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
                    HTTPStatus.OK,
                    payload={"ok": True, "token": cookie_value},
                    headers=[
                        ("Set-Cookie", f"{COOKIE_NAME}={cookie_value}; Path=/; HttpOnly; SameSite=Lax"),
                    ],
                )

            if not _authed(environ, admin_password, session_secret):
                return _json_response(start_response, HTTPStatus.UNAUTHORIZED, {"error": "auth_required"})

            if path == "/admin/api/content" and method == "GET":
                return _json_response(start_response, HTTPStatus.OK, store.load())

            if path == "/admin/api/meta" and method == "GET":
                return _json_response(start_response, HTTPStatus.OK, store.load_meta())

            if path == "/admin/api/publish" and method == "POST":
                return _json_response(start_response, HTTPStatus.OK, store.publish())

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
            if not _authed(environ, admin_password, session_secret):
                return _html_response(start_response, HTTPStatus.OK, _login_page())
            return _html_response(
                start_response,
                HTTPStatus.OK,
                _editor_page(
                    store.load(),
                    _get_query_token(environ) or _get_bearer_token(environ),
                    store.load_meta(),
                ),
            )

        return _json_response(start_response, HTTPStatus.NOT_FOUND, {"error": "not_found"})

    return app
