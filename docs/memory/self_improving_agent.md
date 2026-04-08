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
- Scope: `澶栬锤鍔╃悊_windows_鍐呮祴鍖?app/desktop_app.py` + `app/user_settings.py`
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

## [2026-04-02 23:23:28] harness-finish

- status: success
- summary: Changed scope: 9 file(s); audit=quick. | Core logic preserved: yes. | Core checks pass: 7/7.

## 2026-04-02 - Runtime Gate Variable Drift Guard

- Context: windows release packaging gate (`runtime --audit-level auto`)
- Signal: NameError from stale `rag_db` reference after dual-index refactor
- Rule: when replacing singleton resources with split resources, update all verdict/evidence payload fields in runtime
- Scope: `agent_system/runtime.py` gate + harness verdict generation
- Action: enforce compile/runtime gate check before packaging and keep evidence keys aligned (`rag_db_facts`, `rag_db_memory`)

## 2026-04-02 - API Memory Control Guard

- Context: user expects memory continuity even when local context is disabled
- Signal: conversation continuity expectation not explicit in settings layer
- Rule: expose memory behavior as explicit user setting (on/off + bounded turns)
- Scope: windows desktop API panel + `user_settings.py`
- Action: persist memory switch/turns and pass bounded history window into chat request

## [2026-04-02 23:25:31] harness-finish

- status: success
- summary: Changed scope: 11 file(s); audit=quick. | Core logic preserved: yes. | Core checks pass: 7/7.

## 2026-04-02 - Cross-Platform Update Channel Guard

- Context: build37 windows-first then mac sync
- Signal: mac manual dmg packaging depends on macOS-only tooling, while in-app update only depends on `_mac.zip`
- Rule: prioritize manifest zip assets for one-click update continuity across platforms; treat dmg as secondary manual-install channel
- Scope: `website/api/release-manifest.json` and release packaging workflow
- Action: keep build zip artifacts and manifest entries in lockstep (`_windows.zip`, `_mac.zip`) before any optional dmg step

## [2026-04-03 00:11:32] harness-finish

- status: success
- summary: Changed scope: 11 file(s); audit=quick. | Core logic preserved: yes. | Core checks pass: 7/7.

## 2026-04-05 - Update Manifest Source Decoupling Guard

- Context: build38 release closure across cloud artifacts, website manifest, and in-app one-click update
- Signal: website download files may be published from a separate pipeline/worktree, while the updater only needs stable public asset URLs
- Rule: when release binaries are not guaranteed to be published alongside the tracked website files, point `release-manifest.json` assets to GitHub Release URLs instead of repo-local download paths
- Scope: windows/mac `website/api/release-manifest.json`
- Action: publish cloud-built zip/dmg artifacts to a GitHub Release first, then deploy only the small manifest change

## [2026-04-05 17:44:04] harness-finish

- status: success
- summary: Changed scope: 8 file(s); audit=quick. | Core logic preserved: yes. | Core checks pass: 7/7.

## 2026-04-07 - Local Runtime Integration Guard

- Context: Windows local model support added into the existing API conversation panel
- Signal: local runtimes need different discovery behavior but should not fork the chat feature into a second UX path
- Rule: keep local model support inside the same provider/model/url flow, and reuse existing context, memory, learning, and fallback layers
- Scope: Windows `api_chat.py` + `desktop_app.py`
- Action: local providers may skip API key, but remote provider behavior must remain unchanged and discovery should stay isolated from request formatting

## [2026-04-07 16:28:37] harness-finish

- status: success
- summary: Changed scope: 7 file(s); audit=quick. | Core logic preserved: yes. | Core checks pass: 7/7.

## 2026-04-08 - Nested Repo Isolation Guard

- Context: an unrelated site project was placed under the main workspace root during build39 closure
- Signal: `git status --short` showed an unexpected untracked directory that was actually its own Git repository
- Rule: when an untracked directory has its own `.git`, treat it as a parallel project and isolate it before closure instead of letting it contaminate the current delivery
- Scope: workspace hygiene and release closure
- Action: move nested repos out of the main workspace root or explicitly ignore them before commit

## [2026-04-08 19:36:58] harness-finish

- status: success
- summary: Changed scope: 7 file(s); audit=quick. | Core logic preserved: yes. | Core checks pass: 7/7.
