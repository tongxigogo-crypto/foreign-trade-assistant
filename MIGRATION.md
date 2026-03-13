# Migration Guide

## Workspace

- Root: `E:\CodexWorkspace\Playground\foreign_trade_assistant`

## Required Runtime

- Python 3.10+
- `pip install -r requirements.txt`
- PowerShell for helper scripts
- Google CLI tools:
  - `gcloud`
  - `gws`

## Required Global Skills

- `self-improving-agent`
- `gws-shared`
- `gws-gmail`
- `gws-gmail-send`
- `gws-gmail-triage`
- `gws-gmail-watch`
- `gws-drive`
- `gws-drive-upload`
- `gws-docs`
- `gws-docs-write`
- `gws-sheets`
- `gws-sheets-append`
- `gws-sheets-read`
- `gws-tasks`
- `persona-sales-ops`
- `persona-researcher`
- `persona-project-manager`

## Local Project Assets

- `agents/`
- `app/`
- `data/`
- `docs/memory/`
- `skills/`
- `scripts/`

## Skill Restore

Backup location:

- `E:\CodexWorkspace\SkillBackups\codex-skills-2026-03-13`

Restore one skill:

```powershell
powershell -ExecutionPolicy Bypass -File E:\CodexWorkspace\SkillBackups\codex-skills-2026-03-13\restore-skill.ps1 -Name gws-gmail
```

Restore all backed-up skills:

```powershell
powershell -ExecutionPolicy Bypass -File E:\CodexWorkspace\SkillBackups\codex-skills-2026-03-13\restore-skill.ps1 -All
```

## Google Re-Authorization

Shared auth directory:

- `E:\CodexWorkspace\Playground\shared_google_auth`

Refresh shared Google access:

```powershell
E:\CodexWorkspace\Playground\shared_google_auth\login_full_access.ps1
```

Load a shell-local token:

```powershell
. E:\CodexWorkspace\Playground\shared_google_auth\use_shared_token.ps1
```

Verify Gmail and Drive access:

```powershell
E:\CodexWorkspace\Playground\shared_google_auth\verify_access.ps1
```

## GitHub Re-Authorization

```powershell
& "C:\Program Files\GitHub CLI\gh.exe" auth login
```

## Notion Re-Authorization

- Reconnect Notion from the Codex desktop integration or the configured MCP server.
- Verify access by reading a known page or database after login.

## Validation

Run the project:

```powershell
python -m app.main
```

Run tests:

```powershell
python -m pytest -q
```

## Notes

- Do not rely on copied tokens or stale credentials.
- Re-authorize services on the new machine or account.
- Keep workspace-specific learnings in `docs/memory/self_improving_agent.md`.
