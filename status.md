# 项目状态快照（Status）

更新时间：2026-03-29  
仓库根目录：`E:\CodexWorkspace\Playground-pm`  
当前分支：`codex/product-manager`

## 1) 当前代码进度
- 桌面端已发布 `build16`（版本：`v0.1.1-beta1-build16`）。
- Windows 侧核心流程已回归通过：导入、API 对话、客户详情、看板状态流转。
- Windows 已支持“一键更新”（自动下载 + 就地替换 + 重启），用户无需重复整包下载。
- macOS 已产出 `InVault.app` + `.dmg`，且 App 内置 Python 运行时（用户无需安装 Python/pip）。
- 桌面 UI 已包含：
  - 左侧：启动/导入/雷达检索/扩展安装向导
  - 中间：API 对话（输入/回复/回答依据可调节）
  - 右侧：CRM 风格业务区（客户线、任务看板、事件）
- 客户详情支持业务聚合与可点击打开本地文件（邮件/合同/产品/价格关联信息）。
- Harness 已升级为低 Token 模式（`quick/full/auto` 分级审计、增量摘要、RAG 切片）。

## 2) 核心逻辑（简版）
- 数据主线：
  - 历史资料导入 -> 本地知识库（`knowledge_base.json`）-> 本地上下文注入 API 对话。
- 任务主线：
  - 行动标签执行（报价/跟进等）-> 事件写入 `state_board.json` -> 右侧看板与客户视图联动。
- 桌面优先：
  - 有 API：走桌面主流程（启动、导入、检索、对话、任务流、增长反馈）。
  - 网页端：保留桥接注入与兼容入口，不作为主工作台。
- 配置主线：
  - 正式包默认 `data_dir_mode=system`（用户升级后数据保留在系统目录）。
  - 测试/隔离运行默认 workspace（避免测试串到系统历史数据）。

## 3) 已完成项（最近）
- Windows：一键更新（release-manifest 优先 + 就地替换 + 回滚保护）与 UI 入口调整完成。
- macOS：修复 CI 打包脚本回退问题，恢复产出 `InVault.app` + `.dmg`，并验证 zip 内含内置 Python 运行时。
- 发布收口：已将 build16 产物同步到固定 `release/` 目录并清理归档旧版本。
- 工程：补齐 `docs/harness/*` 作为新线程启动锚点；补齐 `.gitignore`（忽略本地产物/缓存）以减少噪音提交。

## 4) 待办事项（优先级）
- P0（下一版方向）：预留“本地开发 API”（仅本机可访问），为未来企业专属飞书/协作对接提供稳定调用面（UI 给用户、API 给 AI/自动化）。
- P1（企业协作方向）：飞书侧以“多维表格（Bitable）= 指令收件箱/结果回写”作为零自建服务器的主路线（后续按企业专属对接交付）。
- P1：mac 分发体验补齐（Gatekeeper 处理文档 + 评估签名/公证策略）。

## 5) 当前阻塞与风险
- 阻塞：本地到 GitHub `443` 连接间歇失败，git push 不稳定（必要时用 `gh api` 走 git-data API 作为补救通道）。
- 风险：mac 未签名/未公证时，用户端仍可能遇到 Gatekeeper “已损坏/无法打开” 提示（需文档/签名策略降低概率）。

## 6) 验收标准（本轮）
- Windows 包：可双击启动，且不依赖用户本机 Python。
- Mac 包：用户拿到 `.dmg` 后可直接安装 `InVault.app`，无 Python 安装步骤。
- 固定输出目录（build16）：
  - Windows：`E:\CodexWorkspace\Playground-pm\外贸助理_交接包\外贸助理_windows_内测包\release\TA_Beta_v0.1.1-beta1-build16_windows.zip`
  - macOS：`E:\CodexWorkspace\Playground-pm\外贸助理_交接包\外贸助理_mac_内测包\release\TA_Beta_v0.1.1-beta1-build16_mac.dmg`
  - macOS：`E:\CodexWorkspace\Playground-pm\外贸助理_交接包\外贸助理_mac_内测包\release\TA_Beta_v0.1.1-beta1-build16_mac.zip`
- 新线程启动时，仅需读取：
  - `AGENTS.md`
  - `status.md`
  即可恢复开发上下文。
