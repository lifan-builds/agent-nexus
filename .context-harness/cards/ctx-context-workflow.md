---
id: ctx-context-workflow
kind: workflow
importance: 0.9
confidence: confirmed
source: CONTEXT.md#workflow
chunk: null
tokens_est: 63
tags: [context, workflow]
---

# CONTEXT.md: Workflow

## Summary
Setup: pip install pyyaml && python nexus.py init && ln -sf $(pwd)/nexus.py ~/.local/bin/nexus

## Use when
- running, testing, linting, deploying, or verifying changes

## Key facts
- Run: nexus sync --dry-run, then nexus sync after reviewing MCP commands
- Test: nexus doctor
- Lint: ruff check nexus.py (once ruff is added)

## Retrieval order
- Read `NOW.md` and concise `CONTEXT.md` as the always-read layer.
- Use this card before opening bulky `PLAN.md`, chunks, or raw source sections for this topic.
- Open raw detail only when this summary is insufficient for the task.

## Open next only if needed
- `CONTEXT.md#workflow`
