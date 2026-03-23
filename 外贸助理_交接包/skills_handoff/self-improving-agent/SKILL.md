---
name: self-improving-agent
description: Continuous improvement skill for capturing learnings, corrections, failures, and reusable patterns across worktrees. Use when a command or workflow fails unexpectedly, when the user corrects prior output, when repeated mistakes appear, or when a successful pattern should be preserved for future tasks. Use as a global auxiliary skill, but always keep learnings separated by workspace or domain.
---

# Self Improving Agent

Capture durable learnings from execution, not vague reflections.

Use this skill as a global auxiliary layer for any worktree, including:

- foreign trade automation
- short-video production
- new workspaces under `E:\CodexWorkspace\Playground`

Do not mix unrelated domains into one memory file. Keep learnings separated by workspace.

## Core Rule

Install once globally. Apply locally per workspace.

This means:

- one shared skill definition under `$CODEX_HOME/skills`
- separate memory files inside each project or worktree

## When To Write A Learning

Write or update a learning when one of these happens:

1. A command fails because of an environment-specific issue.
2. The user corrects a wrong assumption or output.
3. A workflow succeeds after a non-obvious fix.
4. A repeated preference becomes stable enough to codify.
5. An integration requires a specific local workaround.

Do not create learnings for trivial facts or one-off noise.

## Workspace Separation

Store learnings in one of these files:

- `E:\CodexWorkspace\Playground\foreign_trade_assistant\docs\memory\self_improving_agent.md`
- `E:\CodexWorkspace\Playground\video_workflow\docs\memory\self_improving_agent.md`
- for any new worktree: `<workspace>\docs\memory\self_improving_agent.md`

If the target workspace does not yet contain `docs\memory`, create it.

## Learning Format

Each entry should be concise and actionable.

Use this format:

```markdown
## YYYY-MM-DD - Short Title

- Context: what task or workflow triggered the learning
- Signal: what failed, what was corrected, or what succeeded unexpectedly
- Rule: the durable rule to apply next time
- Scope: which workspace or workflow this applies to
- Action: exact command, path, guardrail, or implementation note
```

## Retrieval Rule

Before starting substantial work in a workspace:

1. Check whether the workspace has `docs\memory\self_improving_agent.md`.
2. Read only the relevant entries for the current task.
3. Apply durable rules, not stale preferences.

Do not bulk-load unrelated history.

## Writing Rule

When adding a learning:

1. Prefer updating an existing entry if the rule already exists.
2. Avoid duplicate lessons with different wording.
3. Keep each rule concrete enough to change behavior.
4. Include exact file paths or commands when they matter.

## Domain Guidance

### Foreign Trade Assistant

Focus on learnings such as:

- Gmail and Drive auth behavior
- CRM contract mismatches
- orchestrator handoff issues
- quotation blocking conditions
- follow-up priority edge cases

### Video Workflow

Focus on learnings such as:

- storyboard toolchain defaults
- Seedance prompt failure patterns
- Blender + Storytools workflow constraints
- recurring IP character consistency rules
- export and edit pipeline issues

## Do Not Do

- Do not overwrite user-authored project documentation.
- Do not store secrets, tokens, raw credentials, or private keys.
- Do not log sensitive email bodies unless the workspace explicitly requires it.
- Do not create “learning” entries that are just status reports.

## Immediate Operating Preference

When both global reuse and domain accuracy matter:

- use one global `self-improving-agent` skill
- keep separate memory files per worktree

This is preferred over creating separate copies of the skill for each workspace, because the method stays consistent while the stored learnings remain isolated.
