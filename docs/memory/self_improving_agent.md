# Self Improving Agent Memory (v2)

This file stores durable, reusable learnings for `E:\CodexWorkspace\Playground-pm`.
Keep entries short, testable, and architecture-focused.

## Write Policy

- Write only when a failure pattern, correction, or strong success pattern is verified.
- Prefer one rule per entry.
- If a rule is obsolete, mark it as retired instead of duplicating contradictory rules.

## Active Rules

## [2026-03-28] single-entry-control-plane

- status: active
- context: historical agent responsibilities were stacked across multiple files and sessions.
- signal: repeated conflicts between old `trade_ops` assumptions and new architecture goals.
- rule: all new agent workflow runs must enter through `agent_system/runtime.py` and its config files.
- scope: E:\CodexWorkspace\Playground-pm
- action: keep legacy orchestration as compatibility only; do not add new responsibilities there.

## [2026-03-28] review-boundary-no-software-edits

- status: active
- context: user requires architecture refactor without touching developed software.
- signal: app/package source files frequently appear dirty in this worktree.
- rule: review tasks must not modify software code under `外贸助理_交接包/*/app` unless explicitly authorized.
- scope: E:\CodexWorkspace\Playground-pm
- action: place architecture changes under `agent_system`, `docs`, `scripts`, and architecture tests only.

## [2026-03-28] harness-first-recovery

- status: active
- context: background compression causes context loss.
- signal: chat-only memory is insufficient across long sessions.
- rule: restore from `docs/harness/session_state.json` and `docs/harness/current_session.md` before substantial work, then checkpoint after runs.
- scope: E:\CodexWorkspace\Playground-pm
- action: keep `architecture_guardrails.json` and `closed_loop_verdict.json` as objective pre/post evidence.

## [2026-03-28] schema-forward-compatible-load

- status: active
- context: user data file may include newly introduced preference fields across versions.
- signal: runtime crash `UserPreference.__init__() got an unexpected keyword argument 'adaptive_profile'`.
- rule: add new dataclass fields explicitly and filter unknown keys during JSON-to-model loading.
- scope: E:\CodexWorkspace\Playground-pm\外贸助理_交接包\外贸助理_windows_内测包\app
- action: keep loaders tolerant to extra fields to avoid breaking upgrades and local memory continuity.

## [2026-03-28] mailbox-imap-ux-disclosure

- status: active
- context: non-technical users interpreted mailbox pull as OAuth login and used normal mailbox passwords.
- signal: repeated pull failures despite valid account due to missing app-password understanding.
- rule: mailbox section must explicitly state current auth mode (`IMAP + app password`) in UI and failure dialogs.
- scope: E:\CodexWorkspace\Playground-pm\外贸助理_交接包\外贸助理_windows_内测包\app
- action: keep guidance near inputs and show targeted remediation on authentication errors.
