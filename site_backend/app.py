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
        "label": "品牌信息",
        "description": "维护站点名称与基础品牌说明。",
        "fields": [
            {"key": "brand_name", "label": "品牌名称", "type": "text", "placeholder": "Tongxi Fairy Lab"},
            {"key": "brand_tagline", "label": "品牌副标题", "type": "textarea", "rows": 3, "placeholder": "宠物 IP · 工具产品 · 国际贸易准备"},
        ],
    },
    {
        "id": "hero",
        "label": "首屏内容",
        "description": "首屏标题区和引导文案。",
        "fields": [
            {"key": "hero_intro", "label": "首屏主介绍", "type": "textarea", "rows": 4},
            {"key": "hero_bridge", "label": "业务关系说明", "type": "textarea", "rows": 4},
            {"key": "hero_summary_title", "label": "首屏摘要标题", "type": "text"},
            {"key": "hero_summary_body", "label": "首屏摘要正文", "type": "textarea", "rows": 4},
        ],
    },
    {
        "id": "pet-ip",
        "label": "Pet IP",
        "description": "管理宠物 IP 模块标题和说明。",
        "fields": [
            {"key": "pet_ip_title", "label": "模块标题", "type": "text"},
            {"key": "pet_ip_body", "label": "模块正文", "type": "textarea", "rows": 5},
        ],
    },
    {
        "id": "trade-assistant",
        "label": "外贸助理",
        "description": "管理外贸助理模块的标题与产品说明。",
        "fields": [
            {"key": "trade_assistant_title", "label": "模块标题", "type": "text"},
            {"key": "trade_assistant_body", "label": "模块正文", "type": "textarea", "rows": 5},
        ],
    },
    {
        "id": "pet-trade",
        "label": "国际贸易",
        "description": "管理国际贸易模块标题和业务方向说明。",
        "fields": [
            {"key": "pet_trade_title", "label": "模块标题", "type": "text"},
            {"key": "pet_trade_body", "label": "模块正文", "type": "textarea", "rows": 5},
        ],
    },
    {
        "id": "mini-program",
        "label": "小程序开发",
        "description": "管理小程序开发能力描述。",
        "fields": [
            {"key": "mini_program_title", "label": "模块标题", "type": "text"},
            {"key": "mini_program_body", "label": "模块正文", "type": "textarea", "rows": 5},
        ],
    },
    {
        "id": "contact",
        "label": "联系方式",
        "description": "管理联系模块标题和说明。",
        "fields": [
            {"key": "contact_title", "label": "模块标题", "type": "text"},
            {"key": "contact_body", "label": "模块正文", "type": "textarea", "rows": 5},
        ],
    },
]


IMAGE_SCHEMA = [
    {"key": "home.hero", "label": "首屏主视觉", "description": "首页第一屏的主插画或主图。"},
    {"key": "home.trade_assistant", "label": "外贸助理配图", "description": "外贸助理模块展示图。"},
    {"key": "home.pet_trade", "label": "国际贸易配图", "description": "国际贸易模块展示图。"},
    {"key": "home.mini_program", "label": "小程序开发配图", "description": "小程序模块展示图。"},
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


def _editor_page(content: dict, auth_token: str | None = None) -> str:
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
      .inspector-panel li {
        margin: 0;
        color: var(--muted);
        font-size: 13px;
        line-height: 1.7;
      }
      .inspector-panel ul {
        margin: 10px 0 0;
        padding-left: 18px;
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
            <button id="save-content" type="button" class="button">保存当前改动</button>
            <button id="reset-content" type="button" class="ghost-button">恢复最近保存版本</button>
            <div id="save-status">当前没有未保存改动。</div>
          </div>
          <div class="stats" id="inspector-stats"></div>
          <div class="inspector-panel">
            <h3>当前区块提示</h3>
            <p id="section-description">选择左侧区块开始编辑。</p>
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
    <script>
      const initialContent = __CONTENT_JSON__;
      const editorSchema = __EDITOR_SCHEMA__;
      const imageSchema = __IMAGE_SCHEMA__;
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
      let dirty = false;

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
          if (field.type === "textarea") {
            return `
              <div class="field-card">
                <label for="${field.key}">${field.label}</label>
                <small>当前编辑 ${currentLang === "zh" ? "中文" : "英文"} 内容</small>
                <textarea id="${field.key}" rows="${field.rows || 4}" data-field="${field.key}" placeholder="${placeholder}">${value}</textarea>
              </div>
            `;
          }
          return `
            <div class="field-card">
              <label for="${field.key}">${field.label}</label>
              <small>当前编辑 ${currentLang === "zh" ? "中文" : "英文"} 内容</small>
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
                <p>${image.description}</p>
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
      }

      function updateTextField(key, value) {
        workingContent.strings[currentLang][key] = value;
        setDirty(true, "检测到文案修改，记得保存。");
      }

      function updateImageField(key, value) {
        workingContent.images[key] = value;
        setDirty(true, "图片路径已更新，保存后前台才会读取到新内容。");
        renderWorkspace();
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
        setDirty(false, "已保存到内容文件。");
        renderAll();
      }

      function resetContent() {
        workingContent = JSON.parse(JSON.stringify(savedContent));
        ensureShape();
        setDirty(false, "已恢复到最近保存版本。");
        renderAll();
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

      renderAll();
    </script>
  </body>
</html>"""
    return (
        template
        .replace("__CONTENT_JSON__", json.dumps(content, ensure_ascii=False))
        .replace("__EDITOR_SCHEMA__", json.dumps(EDITOR_SCHEMA, ensure_ascii=False))
        .replace("__IMAGE_SCHEMA__", json.dumps(IMAGE_SCHEMA, ensure_ascii=False))
        .replace("__TOKEN_JSON__", json.dumps(auth_token or "", ensure_ascii=False))
    )


def create_app(root_dir: Path, admin_password: str, session_secret: str):
    site_dir = root_dir / "website_from_playground"
    store = ContentStore(site_dir)

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
                _editor_page(store.load(), _get_query_token(environ) or _get_bearer_token(environ)),
            )

        return _json_response(start_response, HTTPStatus.NOT_FOUND, {"error": "not_found"})

    return app
