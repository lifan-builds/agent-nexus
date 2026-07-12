---
id: ctx-context-project-structure
kind: project
importance: 0.65
confidence: confirmed
source: CONTEXT.md#project-structure
chunk: null
tokens_est: 155
tags: [context, project-structure, project]
---

# CONTEXT.md: Project Structure

## Summary
nexus.example.yml: Public template manifest checked into the repo.

## Use when
- working on project structure

## Key facts
- nexus.personal.yml: Personal manifest (gitignored). Declares packages, inline MCP servers, optional MCPs, and target IDEs for this machine.
- nexus.example.yml: Example manifest checked into the repo for reference.
- nexus.py: The nexus CLI. Symlinked to ~/.local/bin/nexus for global access. Run nexus sync, nexus list, nexus doctor, nexus clean.
- nexus.sh: Legacy bash CLI (kept as backup, will be removed).
- .nexus/: Local cache directory (gitignored). Contains fetched packages keyed by github.com/org/repo/commit-sha/.

## Retrieval order
- Read `NOW.md` and concise `CONTEXT.md` as the always-read layer.
- Use this card before opening bulky `PLAN.md`, chunks, or raw source sections for this topic.
- Open raw detail only when this summary is insufficient for the task.

## Open next only if needed
- `CONTEXT.md#project-structure`
