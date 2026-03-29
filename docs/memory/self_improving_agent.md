# Self Improving Agent Memory

This file stores reusable learnings, corrections, and failure patterns for this worktree only.


## [2026-03-17 00:58:09] trade-ops-run

- status: needs_confirmation
- summary: Preview mode blocked write operations for 2026-03-17.

## [2026-03-29 22:57:39] harness-finish

- status: degraded
- summary: agent_system/runtime.py missing; memory-only writeback applied

## [2026-03-29 23:13:46] harness-finish

- status: success
- summary: Changed scope: 19 file(s); audit=quick. | Core logic preserved: yes. | Core checks pass: 7/7.

## 2026-03-30 - Mac Build Release Guardrails

- Context: Repeated mac beta packaging and runtime fixes across `build20` to `build28`, including popup storms, wrong app entry routing, SSL trust, and file-import support.
- Signal: Several mac builds looked "successful" in CI but still shipped broken runtime behavior because the root cause was in the frozen app entry path or unsupported importer formats, not just packaging.
- Rule: For mac releases in this workspace, do not claim a fix from source edits alone; always verify the exact frozen runtime path and align UI claims with actual importer capabilities before publishing.
- Scope: `E:\CodexWorkspace\Playground-pm` mac desktop beta workflow.
- Action: Keep `外贸助理_交接包\外贸助理_mac_内测包\app\desktop_entry.py` routing `cli ...` arguments into `run_cli(args[1:])`; keep `外贸助理_交接包\外贸助理_mac_内测包\app\history_importer.py` and `外贸助理_交接包\外贸助理_mac_内测包\app\desktop_app.py` synchronized; after tagging, verify GitHub Actions run success and copy artifacts into `外贸助理_交接包\外贸助理_mac_内测包\release`.
