# Self Improving Agent Memory

This file stores reusable learnings for `E:\CodexWorkspace\Playground-pm` only.

## 2026-03-17 - Preview Write Guard

- Context: trade-ops run in preview mode
- Signal: write operations were blocked by execution mode
- Rule: verify run mode before expecting persistent write outputs
- Scope: this workspace runtime harness
- Action: check mode first, then execute write-required workflows

## 2026-03-29 - Harness Baseline Integrity

- Context: harness finish stage
- Signal: runtime file mismatch produced degraded completion
- Rule: treat `status.md` and `docs/harness/*` as non-deletable anchors
- Scope: end-of-run cleanup and closure
- Action: validate existence of baseline files before reporting completion

## 2026-03-30 - Mac Release Verification Guardrail

- Context: repeated mac beta builds from build20 to build28
- Signal: CI success did not guarantee runtime correctness in frozen app path
- Rule: do not claim mac fix complete from source edits only
- Scope: mac desktop beta packaging workflow
- Action: verify frozen runtime behavior + UI claim alignment + artifact sync to fixed `release` folder

## 2026-03-30 - Import Parser Exception Isolation

- Context: users imported mixed folders containing malformed office files
- Signal: errors like `File is not a zip file` and `list index out of range` aborted the full batch
- Rule: importer loops must isolate per-file parse exceptions and continue
- Scope: `history_importer.py` in mac/windows package trees
- Action: keep regression tests for parser failures and rerun them for both package trees before shipping

## [2026-03-30 02:24:47] harness-finish

- status: success
- summary: Changed scope: 2 file(s); audit=quick. | Core logic preserved: yes. | Core checks pass: 7/7.

## [2026-03-30 12:37:02] harness-finish

- status: success
- summary: Changed scope: 11 file(s); audit=quick. | Core logic preserved: yes. | Core checks pass: 7/7.

## [2026-03-30 12:56:02] harness-finish

- status: success
- summary: Changed scope: 6 file(s); audit=quick. | Core logic preserved: yes. | Core checks pass: 7/7.

## [2026-03-30 13:09:54] harness-finish

- status: success
- summary: Changed scope: 5 file(s); audit=quick. | Core logic preserved: yes. | Core checks pass: 7/7.

## 2026-03-30 - Version/Manifest Consistency Guard

- Context: release package names moved ahead while in-app version constants lagged on beta1 build19
- Signal: package filename/version and app runtime version diverged, causing update and verification ambiguity
- Rule: when bumping release build tags, update `app/version.py` and `website/api/release-manifest.json` in mac/windows together before packaging
- Scope: beta packaging + auto-update pipeline
- Action: enforce a pre-build checklist item for version constant + manifest consistency

## 2026-04-02 - Provider/Model and Theme UX Guard

- Context: windows desktop settings usability and release-readiness round
- Signal: provider switch left stale model; update flow required extra confirmation; visual mode lacked system/light/dark options
- Rule: provider changes must atomically sync URL+model defaults; one-click update should be single-intent flow; theme preference must be persistent and reversible
- Scope: `外贸助理_windows_内测包/app/desktop_app.py` + `app/user_settings.py`
- Action: add regression tests for provider-model linkage and theme-mode persistence before syncing to mac

## [2026-04-02 00:59:47] harness-finish

- status: success
- summary: Changed scope: 8 file(s); audit=quick. | Core logic preserved: yes. | Core checks pass: 7/7.

## 2026-04-02 - Architecture Focus Guard (Depth Before Breadth)

- Context: roadmap decision for next stage after windows build32 closure
- Signal: user concern on privacy-boundary complexity for enterprise chat ingestion
- Rule: when compliance/permission boundary is unclear, prioritize core assistant quality stack first (evaluation harness + preference learning + retrieval quality)
- Scope: roadmap planning for this workspace
- Action: execute 1) eval harness, 2) self-improving v1, 3) rag dual-index, 4) model adapter before expanding ingestion channels

## [2026-04-02 02:58:41] harness-finish

- status: success
- summary: Changed scope: 4 file(s); audit=quick. | Core logic preserved: yes. | Core checks pass: 7/7.
