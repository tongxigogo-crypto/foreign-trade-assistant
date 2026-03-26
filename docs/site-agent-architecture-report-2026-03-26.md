# Site Publishing Agent 架构优化说明（2026-03-26）

## 目标

为个人网站部署与迭代建立专业化多 Agent 协作体系，并明确适配 Google Stitch 的 UI 美化职责。

## 本次补充

1. 角色体系升级  
- 新增并固化 `ui_stitch_agent`，用于 Stitch 驱动的 UI 精修与交接。
- 将工作树角色定义切换为网站发布链路：strategy/content/seo/ui/implementation/qa/release/analytics。

2. 运行配置与契约  
- `site_ops/config/agent-registry.json`
- `site_ops/config/publishing-policy.json`
- `site_ops/config/stitch-integration.json`
- `site_ops/contracts/agent-envelope.schema.json`
- `site_ops/contracts/workflow-report.schema.json`

3. 专用编排入口  
- `site_ops/orchestrator.py`
- `scripts/site-publishing-run.ps1`

4. 自动化验证  
- `tests/test_site_publishing_orchestrator.py`

## Stitch 适配职责

`ui_stitch_agent` 的核心职责：
- 将视觉优化请求转成 Stitch 可执行任务。
- 输出实现交接所需材料：
  - stitch_export_reference
  - component_map
  - style_tokens
  - responsive_notes
- 在发布前与 QA 协作完成桌面/移动端与对比度检查。

## 迁移策略

- 非破坏式：保留现有 `trade_ops` 模板文件不动。
- 增量启用：新工作流统一走 `site_ops`。
- 后续可逐步移除 `trade_ops` 残留模板资产。
