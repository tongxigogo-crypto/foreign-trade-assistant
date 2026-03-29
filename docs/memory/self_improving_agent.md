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
