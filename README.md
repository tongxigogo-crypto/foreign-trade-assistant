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

## Product calculator

`product-calculator/` is a standalone offline material take-off tool: a
calculation engine plus a UI skeleton, with one explicitly fictional example
product. Open `product-calculator/index.html` by double-click — no server, no
dependencies, no network.

It ships no product data by design. See `product-calculator/README.md` before
filling in real specifications, and `product-calculator/规则说明.md` for the
formula table that must be confirmed before any real quotation.

## Structure

- `agents/`: role definitions and contracts
- `.codex/config.toml`: routing and coordination settings
- `app/`: implementation
- `data/`: sample business data and generated summaries
- `logs/`: runtime logs
- `tests/`: automated tests
