## 2026-03-16 - GWS auth persistence workaround for this workspace

- Context: Workspace needed stable Gmail/Drive execution under `suqiong.cn@gmail.com`.
- Signal: `gws auth login` repeatedly completed browser callback (`localhost ... Success`) but did not persist credentials (`auth_method: none`).
- Rule: In this workspace, do not rely on `gws auth login` local credential persistence as primary path.
- Scope: `E:\CodexWorkspace\Playground\foreign_trade_assistant` foreign-trade operations.
- Action:
  - Use `gcloud auth application-default login --client-id-file <client_secret.json> --scopes "https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/gmail.readonly,https://www.googleapis.com/auth/drive.readonly,https://www.googleapis.com/auth/userinfo.email,openid"`.
  - For `gws` calls, set `GOOGLE_WORKSPACE_CLI_TOKEN` from `gcloud auth application-default print-access-token`.
  - If authorization fails, clear stale `gws` processes before retrying to avoid localhost callback conflicts.

## 2026-03-16 - Knowledge scoping rule for trade assistant

- Context: User requested persistent worktree intelligence for foreign-trade assistant.
- Signal: Drive contains mixed domains; AI video assets should not influence trade responses.
- Rule: Keep default response scope to export-trade operations and exclude AI video corpus unless explicitly requested.
- Scope: This workspace only.
- Action:
  - Always load `trade_ops/config/foreign-trade-worktree.md` for business Q&A.
  - Prioritize `trade_ops/config/pricing-rules.json` and latest `trade_ops/output/*` during recommendations.

## 2026-03-16 23:14:44 - trade_ops_pipeline
- Category: success
- Trigger: automatic self-improving hook.
- status=success
- Scope: foreign_trade_assistant
- note: none


## 2026-03-16 23:15:30 - enable_auto_self_improve
- Category: correction
- Trigger: automatic self-improving hook.
- status=success
- Scope: foreign_trade_assistant
- note: Auto hook enabled in AGENTS and trade-ops skill

## 2026-03-16 - Weekly backup guardrail against accidental deletion

- Context: User required a durable prevention mechanism after accidental workspace deletion.
- Signal: Existing project could be modified rapidly and needed automated rollback points.
- Rule: Keep a scheduled weekly full-project zip backup with retention, and verify creation immediately after setup.
- Scope: `E:\CodexWorkspace\Playground\foreign_trade_assistant` workspace protection.
- Action:
  - Maintain script at `E:\CodexWorkspace\Playground\foreign_trade_assistant\scripts\weekly_backup.ps1`.
  - Keep scheduled task `ForeignTradeAssistantWeeklyBackup` (Friday 21:00).
  - Store archives and log under `E:\CodexWorkspace\Backups\foreign_trade_assistant\`.
  - On backup-task changes, run one manual backup and check `backup.log`.

## 2026-03-16 - Local homepage prototype delivery pattern

- Context: User requested immediate local preview for independent-site homepage design.
- Signal: Text-only proposals were insufficient; user needed click-open visual output.
- Rule: Deliver a runnable local HTML prototype first, then iterate copy/branding on top.
- Scope: Foreign-trade website pre-sales/marketing content workflow.
- Action:
  - Keep preview file at `E:\CodexWorkspace\Playground\site-preview\index.html`.
  - Use section order matching Western B2B scan behavior: Hero -> Proof -> Product Entry -> Why Us -> FAQ -> CTA.
  - Keep copy in English by default for international buyer-facing pages.


## 2026-03-16 23:37:03 - daily_learning_summary
- Category: success
- Trigger: automatic self-improving hook.
- status=success
- Scope: foreign_trade_assistant
- note: Compiled daily learnings into memory docs,Added reusable backup and local preview patterns

