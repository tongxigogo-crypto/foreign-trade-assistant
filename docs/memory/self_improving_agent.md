# Self Improving Agent Memory

This file stores reusable learnings, corrections, and failure patterns for this worktree only.


## [2026-03-27] harness-recovery-anchor

- Context: The user asked to prevent memory loss after background compression.
- Signal: Long-running development sessions need a durable recovery anchor outside chat context.
- Rule: Use `docs/harness/session_state.json` as the primary restore point, `docs/harness/current_session.md` as the readable checkpoint, and update both after substantial runs before reporting back.
- Scope: E:\CodexWorkspace\Playground-pm
- Action: Restore from harness state first, then supplement with memory and git status.


## [2026-03-17 00:58:09] trade-ops-run

- status: needs_confirmation
- summary: Preview mode blocked write operations for 2026-03-17.

## [2026-03-27] software-dev-only-boundary

- Context: User clarified that website download page and repository synchronization will be handled by other worktrees.
- Signal: Current worktree should not touch release publishing or website sync anymore.
- Rule: Keep this worktree focused on software development, packaging, and local verification only.
- Scope: E:\CodexWorkspace\Playground-pm / 澶栬锤鍔╃悊_浜ゆ帴鍖?- Action: Do not modify website download pages, repository publishing assets, or cross-worktree release sync in this workspace unless the user explicitly reassigns that responsibility.

## [2026-03-27] stable-project-rules

- Context: User asked to stop repeating the same workspace rules, directories, and delivery constraints.
- Signal: Repeated clarification overhead should be removed from future turns.
- Rule: Treat the following as default working memory for this workspace: main development stays in `E:\CodexWorkspace\Playground-pm\澶栬锤鍔╃悊_浜ゆ帴鍖匼澶栬锤鍔╃悊_windows_鍐呮祴鍖卄; Mac mirrors the same codebase; website sync/repo publishing belong to other worktrees; delivery artifacts go to `E:\CodexWorkspace\TradeAssistant_delivery_latest`; avoid shipping test API keys; keep a single user-guide TXT; maintain build-numbered incremental releases.
- Scope: E:\CodexWorkspace\Playground-pm / 澶栬锤鍔╃悊_浜ゆ帴鍖?- Action: Do not ask the user to restate these defaults unless the requested task explicitly conflicts with them.

## [2026-03-27] proactive-memory-updates

- Context: User clarified that this memory file is not a passive note pad.
- Signal: The agent should not wait to be prompted before writing durable learnings.
- Rule: After each substantial run, proactively record reusable findings, corrected assumptions, repeated failures, workflow deviations, and stable preferences into this workspace memory file.
- Scope: E:\CodexWorkspace\Playground-pm / 澶栬锤鍔╃悊_浜ゆ帴鍖?- Action: Update `docs\memory\self_improving_agent.md` immediately when a lesson is durable enough to prevent future repetition or error.

## [2026-03-27] commit-hygiene-and-scope

- Context: User defined how to group commits and which files must never be committed.
- Signal: Same-target changes should be committed together, but noise files and unrelated purpose changes must stay out of the same commit.
- Rule: Commit only coherent change sets; never commit `__pycache__`, build artifacts, temporary exports, IDE caches, or obvious local-only files; separate architecture refactors, doc updates, website handoff, and cache cleanup into different commits; if a pile of uncommitted changes exists, classify their source first and only touch the user-owned or newly requested scope unless explicit confirmation covers the rest.
- Scope: E:\CodexWorkspace\Playground-pm / 澶栬锤鍔╃悊_浜ゆ帴鍖?- Action: Before any future commit or cleanup, sort changes by origin and purpose, then keep unrelated leftovers untouched unless the user explicitly asks to fold them in.

## [2026-03-27] runtime-state-is-not-source

- Context: The worktree repeatedly accumulates `local_data/` state files, build caches, and generated download folders that are useful at runtime but should not be treated as source changes.
- Signal: Deleting obvious caches is safe, but runtime state such as `local_data/` should usually stay uncommitted and be treated as local working data unless the user explicitly asks to package or snapshot it.
- Rule: Prefer recursive cleanup of `__pycache__`, duplicate build output, and generated download assets; keep runtime state out of commits; if a cleanup script itself causes new cache folders to appear, rerun a repository-wide recursive scan before concluding cleanup is complete.
- Scope: E:\CodexWorkspace\Playground-pm / 澶栬锤鍔╃悊_浜ゆ帴鍖?- Action: Treat `local_data/` as runtime state by default and separate it from source control decisions.

## [2026-03-27] commit-checkpoint-flow

- Context: The user wants commit hygiene to be part of the agent workflow, not a one-off reminder.
- Signal: After a substantial run, the agent should inspect `git status --short` before finishing and make an explicit judgment: commit-ready coherent change set, still-in-progress work, or pure noise that should be cleaned.
- Rule: Treat functional closure, test pass status, theme cohesion, and single-revertability as commit checkpoint criteria; when the criteria are met, prompt to鏀跺彛鎻愪氦; when the work is exploratory or partial, say to continue; when the status is mostly caches/build noise, say to clean instead of commit.
- Scope: E:\CodexWorkspace\Playground-pm / 澶栬锤鍔╃悊_浜ゆ帴鍖?- Action: Keep the submit/cleanup decision in the workflow, not only in memory.

## [2026-03-27] language-toggle-needs-full-widget-coverage

- Context: The English toggle only partially translated the desktop window because several sections were built with local-only labels/buttons and never stored as attributes for later refresh.
- Signal: If a screen supports runtime language switching, every visible label/button/section title that should change language must be kept as a reusable widget reference or routed through a shared text map.
- Rule: When adding or revising language switching, first audit the whole window for text-bearing widgets, store reusable references during build, then update both zh and en branches symmetrically; add a regression test that checks the previously missed sections.
- Scope: E:\CodexWorkspace\Playground-pm / 澶栬锤鍔╃悊_浜ゆ帴鍖?- Action: Treat partial translation as a widget-coverage bug, not a copy-text bug.

## [2026-03-27] mac-build-fallback-in-windows-runner

- Context: Mac package build is often triggered from a non-mac host where `python3 -m venv` may fail due to missing `ensurepip/python3-venv`.
- Signal: Build script should not hard-fail if venv bootstrap is unavailable in this environment.
- Rule: Keep `build_mac_release.sh` resilient: when venv bootstrap fails, continue assembling a source-only offline package and clearly print `BUILD_MODE=source_only`; use `python3` in zip fallback path for cross-host compatibility.
- Scope: E:\CodexWorkspace\Playground-pm / 澶栬锤鍔╃悊_浜ゆ帴鍖?- Action: Distinguish source-only package from native mac binary package in logs and release expectations.

## [2026-03-27] desktop-i18n-placeholder-sync

- Context: EN switch still showed Chinese for radar/import default placeholder texts even after label translations were complete.
- Signal: Tk Text widgets append trailing newline; exact-string placeholder matching misses updates.
- Rule: For runtime placeholder localization, compare both raw value and .strip() value before deciding whether to replace defaults.
- Scope: E:\CodexWorkspace\Playground-pm / 外贸助理_交接包
- Action: Keep placeholder defaults as explicit zh/en constants and run a language-switch contract test that checks placeholder/body/status strings, not only button labels.

## [2026-03-27] mac-distribution-must-be-native-for-nontechnical-users

- Context: Script-based mac zip caused repeated Gatekeeper/permissions/support failures for nontechnical seed users.
- Signal: If target users are nontechnical, Launch + pip/bootstrap flow is not acceptable as primary distribution.
- Rule: Mac release pipeline should produce native .app and .dmg artifacts on macos-latest; script-based packages are fallback for internal technical testing only.
- Scope: E:\CodexWorkspace\Playground-pm / 外贸助理_交接包
- Action: Keep updater launcher detection compatible with .app bundles in update zips.

## [2026-03-27] office-import-regression-guard

- Context: User required history import to support `pdf/ppt` and other Office formats, and incremental import had shown false zero-import behavior.
- Signal: Import capability was implemented but lacked dedicated regression tests, creating risk of future accidental rollback.
- Rule: Keep `xlsx/docx/pptx/pdf` import support in both Windows and Mac importers, and maintain explicit tests in Windows package (`test_history_importer_office.py`) for suffix scanning and extraction behavior.
- Scope: E:\CodexWorkspace\Playground-pm / 外贸助理_交接包
- Action: When changing importer logic, run office-import tests before packaging and release.


## [2026-03-27T18:51:54+08:00] updated self-improving memory

- status: checkpoint
- summary: Harness recovery anchor added for session restoration after background compression.

## [2026-03-27T18:59:01+08:00] added tests for guardrails and closed-loop checks

- status: checkpoint
- summary: Added preflight architecture guardrails and post-run closed-loop evidence so sessions can restore from durable files after compression.

## [2026-03-27T19:00:06+08:00] added schema alignment into guardrails

- status: checkpoint
- summary: Added preflight architecture guardrails and post-run closed-loop evidence, including schema alignment checks, so sessions can restore from durable files after compression.

## [2026-03-27T19:00:44+08:00] added schema alignment into guardrails

- status: checkpoint
- summary: Added preflight architecture guardrails, post-run closed-loop evidence, schema alignment checks, and pytest collection scoping so sessions can restore and validate cleanly after compression.
