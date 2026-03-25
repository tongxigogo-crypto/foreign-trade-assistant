# 外贸助理网站部署（Vercel）

## 部署目录
- `website/` 目录（当前路径见下方）

## 一次性部署步骤
1. 登录 Vercel，选择 `New Project`。
2. 连接仓库 `tongxigogo-crypto/foreign-trade-assistant`。
3. 在 `Root Directory` 里选择：
   - `外贸助理_交接包/外贸助理_windows_内测包/website`
4. Framework 选择 `Other`（静态站点）。
5. 点击 `Deploy`。

## 发布后检查
- 首页：`/`
- 下载页：`/download.html`
- Agent 元数据：`/.well-known/agent.json`
- OpenAPI 占位：`/api/openapi.json`
- LLM 说明：`/llms.txt`

## 版本更新方式
- 只改 `api/release-manifest.json` 的 `version` 与下载 URL，网站下载按钮会自动更新。

## 中英文切换
- 页面右上角按钮切换，默认中文。
- 名称固定：中文 `外贸助理`，英文 `Trade Assistant`。
