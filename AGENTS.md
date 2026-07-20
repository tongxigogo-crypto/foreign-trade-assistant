# 网站发布多 Agent 工作区

## 使命

通过协调一致的专业 Agent 系统，构建、部署并迭代改进个人网站。

## 启动优先级

在此 worktree 中开始任何新对话时，请首先按以下顺序阅读这些来源：

1. `AGENTS.md`
2. `docs/memory/self_improving_agent.md`
3. `site_ops/config/site-strategy.md`
4. `site_ops/config/publishing-policy.json`
5. `docs/team-knowledge/INDEX.md`
6. `site_ops/output/` 下的最新输出

## 必需的 Agent

- orchestrator
- strategy_agent
- content_agent
- seo_agent
- ui_stitch_agent
- implementation_agent
- qa_agent
- release_agent
- analytics_agent

## 协作规则

- Orchestrator 是唯一的端到端工作流协调者。
- 专业 Agent 应专注于各自领域，并在缺少数据时返回结构化状态。
- 共享业务对象应只定义一次并重复使用。
- 机器间交接必须优先采用结构化输出。
- 任何发布或部署建议都应先以草案形式提出，并通过确认门控制。
- `ui_stitch_agent` 负责基于 Stitch 的 UI 润色，并交付可直接实施的产物。

## 工程纪律

- 将 `karpathy-style-engineering` 作为此 worktree 中实施、调试和审查工作的全局执行约束。
- 编码前，重新陈述目标结果，明确重要假设；只有当缺失信息会实质性改变解决方案时才优先提问。
- 优先采用满足既定目标的最简单有效方案；避免推测性抽象、框架反复更换以及扩大相邻范围。
- 保持差异范围精简：除非存在直接阻塞问题而不得不扩大修改，否则只触及任务所需的文件和代码路径。
- 未针对请求的结果进行具体验证，不得声称完成；如果仅完成部分验证，应明确说明仍存在的假设或风险。

## 事实来源

- 产品及品牌意图以 `site_ops/config/site-strategy.md` 为准
- 发布策略以 `site_ops/config/publishing-policy.json` 为准
- Stitch UI 润色规则以 `site_ops/config/stitch-integration.json` 为准
- 仓库代码是已发布网站行为的事实来源
- 在发布确认前，性能和内容结果仅作为建议

## 范围控制

- 默认范围仅限个人网站的发布和迭代。
- 除非明确要求，否则排除外贸工作流。
- 确保每个发布周期都可审计、可回退。

## 安全规则

- 切勿提交密钥、令牌、密码或原始凭据。
- 从 `.env` 或密钥存储中加载敏感值。
- 在日志中遮蔽敏感值。

## 用户确认门

- 保持 self-improving 调用处于启用状态。
- 修改仓库文件时，保持自动 git commit 处于启用状态。
- 任何影响发布的操作都必须先获得用户明确确认。
- 向 `site_ops/output/` 写入文件或更改运行时状态，必须先获得明确确认。

## Self-Improving 规则

- 不要等待用户提出记忆更新请求。
- 在任何实质性运行之后，主动将可复用的经验、修正后的假设和重复出现的失败模式记录到 `docs/memory/self_improving_agent.md`。
- 如果某项规则、工作流或输出模式被证明有用，应立即将其持久化到 worktree 中。
- 不要在每次运行后机械地迭代 Agent 系统。应先汇总新证据，将可复用经验与一次性任务细节分开；只有当经验会改变未来执行时，才更新记忆或 harness 规则。
- 根据观察到的真实 Agent 执行改进 harness：在修改编排代码或契约之前，记录所选专业 Agent、任务边界、交接形式、验证证据，以及失败或确认行为。

## 团队共享知识

- 固定版本的共享知识库位于 `docs/team-knowledge/`。
- 完成本项目的本地启动文件读取后，读取 `docs/team-knowledge/INDEX.md`，
  并且只加载适用于 `site-publishing` 和当前任务的已批准条目。
- 本项目策略、发布策略、仓库代码和本地验证证据与共享知识冲突时，
  以项目本地事实来源为准。
- `docs/team-knowledge/proposals/` 仅是待审核参考；未经人工提升，不得据此
  改变发布、部署或运行时行为。
- 可跨项目复用的经验应在 `tong-codex/team-codex-knowledge` 中通过独立分支
  和 Pull Request 提交；不要在 detached 状态下直接修改子模块。
- 克隆后如果目录缺失，先执行 `git submodule update --init --recursive`。
- 不得向共享知识库同步 Codex sessions、凭据、私人聊天导出、原始媒体或
  仅存在于未提交工作区的证据。


## 自主并行规则

- Orchestrator 应主动判断当前任务何时适合使用子 Agent。
- 当工作可自然拆分为独立的策略、内容、SEO、UI、实施、QA、发布或分析轨道时，不要等待用户提出使用子 Agent 的请求。
- 只调度最少且有用的专业 Agent。已注册的完整 Agent 名单是能力图谱，并不意味着每项任务都必须调用所有角色。
- 对于可自然拆分的中型或大型任务，只并行运行相互独立的专业轨道，然后由 orchestrator 汇总其输出。
- 子 Agent 工作应范围明确、结构化且可审计。
- 无需用户提醒；在此 worktree 中，主动编排子 Agent 是预期行为。

## Harness 改进规则

- 将 `site_ops/config/agent-registry.json` 视为可用角色注册表，而不是某个角色已执行的证明。
- harness 更新必须基于一次真实运行，并应记录：任务类型、实际使用的 Agent、选择各 Agent 的原因、结构化交接、完成的验证，以及任何阻塞性的确认门。
- 优先进行小范围的契约、测试或路由改进，以修复观察到的缺口。不要添加推测性的角色、状态、产物或工作流分支。
- 在报告和交接中，应区分仓库声明的 Agent 与实际调度的 Agent。
