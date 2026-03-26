# Self Improving Agent Memory

This file stores reusable learnings, corrections, and failure patterns for this worktree only.


## [2026-03-17 00:58:09] trade-ops-run

- status: needs_confirmation
- summary: Preview mode blocked write operations for 2026-03-17.

## [2026-03-27] software-dev-only-boundary

- Context: User clarified that website download page and repository synchronization will be handled by other worktrees.
- Signal: Current worktree should not touch release publishing or website sync anymore.
- Rule: Keep this worktree focused on software development, packaging, and local verification only.
- Scope: E:\CodexWorkspace\Playground-pm / 外贸助理_交接包
- Action: Do not modify website download pages, repository publishing assets, or cross-worktree release sync in this workspace unless the user explicitly reassigns that responsibility.

## [2026-03-27] stable-project-rules

- Context: User asked to stop repeating the same workspace rules, directories, and delivery constraints.
- Signal: Repeated clarification overhead should be removed from future turns.
- Rule: Treat the following as default working memory for this workspace: main development stays in `E:\CodexWorkspace\Playground-pm\外贸助理_交接包\外贸助理_windows_内测包`; Mac mirrors the same codebase; website sync/repo publishing belong to other worktrees; delivery artifacts go to `E:\CodexWorkspace\TradeAssistant_delivery_latest`; avoid shipping test API keys; keep a single user-guide TXT; maintain build-numbered incremental releases.
- Scope: E:\CodexWorkspace\Playground-pm / 外贸助理_交接包
- Action: Do not ask the user to restate these defaults unless the requested task explicitly conflicts with them.

## [2026-03-27] proactive-memory-updates

- Context: User clarified that this memory file is not a passive note pad.
- Signal: The agent should not wait to be prompted before writing durable learnings.
- Rule: After each substantial run, proactively record reusable findings, corrected assumptions, repeated failures, workflow deviations, and stable preferences into this workspace memory file.
- Scope: E:\CodexWorkspace\Playground-pm / 外贸助理_交接包
- Action: Update `docs\memory\self_improving_agent.md` immediately when a lesson is durable enough to prevent future repetition or error.

## [2026-03-27] commit-hygiene-and-scope

- Context: User defined how to group commits and which files must never be committed.
- Signal: Same-target changes should be committed together, but noise files and unrelated purpose changes must stay out of the same commit.
- Rule: Commit only coherent change sets; never commit `__pycache__`, build artifacts, temporary exports, IDE caches, or obvious local-only files; separate architecture refactors, doc updates, website handoff, and cache cleanup into different commits; if a pile of uncommitted changes exists, classify their source first and only touch the user-owned or newly requested scope unless explicit confirmation covers the rest.
- Scope: E:\CodexWorkspace\Playground-pm / 外贸助理_交接包
- Action: Before any future commit or cleanup, sort changes by origin and purpose, then keep unrelated leftovers untouched unless the user explicitly asks to fold them in.

## [2026-03-27] runtime-state-is-not-source

- Context: The worktree repeatedly accumulates `local_data/` state files, build caches, and generated download folders that are useful at runtime but should not be treated as source changes.
- Signal: Deleting obvious caches is safe, but runtime state such as `local_data/` should usually stay uncommitted and be treated as local working data unless the user explicitly asks to package or snapshot it.
- Rule: Prefer recursive cleanup of `__pycache__`, duplicate build output, and generated download assets; keep runtime state out of commits; if a cleanup script itself causes new cache folders to appear, rerun a repository-wide recursive scan before concluding cleanup is complete.
- Scope: E:\CodexWorkspace\Playground-pm / 外贸助理_交接包 - Action: Treat `local_data/` as runtime state by default and separate it from source control decisions.

## [2026-03-27] commit-checkpoint-flow

- Context: The user wants commit hygiene to be part of the agent workflow, not a one-off reminder.
- Signal: After a substantial run, the agent should inspect `git status --short` before finishing and make an explicit judgment: commit-ready coherent change set, still-in-progress work, or pure noise that should be cleaned.
- Rule: Treat functional closure, test pass status, theme cohesion, and single-revertability as commit checkpoint criteria; when the criteria are met, prompt to收口提交; when the work is exploratory or partial, say to continue; when the status is mostly caches/build noise, say to clean instead of commit.
- Scope: E:\CodexWorkspace\Playground-pm / 外贸助理_交接包 - Action: Keep the submit/cleanup decision in the workflow, not only in memory.
