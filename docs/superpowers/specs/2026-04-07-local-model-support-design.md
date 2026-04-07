# Windows Local Model Support Design

## Goal

在 Windows 版现有“对话中枢（API）”里增加本地模型使用能力，不新增第二套聊天入口。

## Scope

- 仅本轮实现 Windows。
- 新增本地 provider：
  - `local_ollama`
  - `local_openai`
- 支持自动探测本地服务、拉取模型列表、无 API Key 调用本地模型。
- 保持现有能力不回归：
  - 本地上下文
  - 会话记忆
  - 学习改写
  - 本地资料缺失时联网兜底

## Architecture

### UI

- 继续使用 `desktop_app.py` 的现有 API 面板。
- `Provider` 下拉框新增两个 provider。
- `Model` 输入框升级为可输入的 `Combobox`，允许：
  - 手动输入模型名
  - 刷新后从本地模型列表选择
- 增加 `Refresh Models` 按钮：
  - 仅本地 provider 可用
  - 远程 provider 时禁用
- `API Key` 在本地 provider 时允许为空，并在 UI 上禁用输入。

### Chat Runtime

- `api_chat.py` 继续作为统一聊天入口。
- 远程 provider 维持现状。
- `local_openai`：
  - 复用现有 OpenAI-compatible 请求格式
  - 默认地址优先指向本地服务
  - 不发送 `Authorization` 头（若 key 为空）
- `local_ollama`：
  - 聊天同样走 OpenAI-compatible 请求格式
  - 模型发现单独调用 Ollama `/api/tags`
  - 默认聊天地址走 `http://127.0.0.1:11434/v1/chat/completions`

### Discovery

- `local_ollama` 探测地址：
  - `http://127.0.0.1:11434`
  - `http://localhost:11434`
- `local_openai` 探测地址：
  - `http://127.0.0.1:1234/v1`
  - `http://localhost:1234/v1`
  - `http://127.0.0.1:8000/v1`
  - `http://localhost:8000/v1`
- 模型列表接口：
  - `local_ollama` -> `/api/tags`
  - `local_openai` -> `/models`

## Error Handling

- 本地服务不可达：明确报错，不自动切远程。
- 模型不存在：明确报错。
- 模型列表为空：允许保存与测试，但提示“未发现已安装模型”。

## Testing

- `test_api_chat.py`
  - 本地 provider 默认 URL
  - 本地模型列表拉取
  - 本地 provider 无 key 时不发送授权头
- 现有远程 provider 请求不回归

## Out of Scope

- 本地模型下载/安装管理
- 扫描磁盘模型文件
- mac 同步
