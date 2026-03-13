# AI Trade Multi-Agent System

## Run

```bash
python -m app.main
```

## Test

```bash
python -m pytest -q
```

## Shared Google Auth

This worktree can reuse the shared Google authorization stored under:

- `E:\CodexWorkspace\Playground\shared_google_auth`

PowerShell:

```powershell
. .\scripts\use_shared_google_auth.ps1
```

If Gmail and Drive scopes need to be refreshed, run:

```powershell
E:\CodexWorkspace\Playground\shared_google_auth\login_full_access.ps1
```

## Global Auxiliary Skill

This worktree can use the global `self-improving-agent` skill.

Workspace-local learnings should be written to:

- `docs/memory/self_improving_agent.md`

## Structure

- `agents/`: role definitions and contracts
- `.codex/config.toml`: routing and coordination settings
- `app/`: implementation
- `data/`: sample business data and generated summaries
- `logs/`: runtime logs
- `tests/`: automated tests
