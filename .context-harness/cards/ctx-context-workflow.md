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
- running, testing, linting, deploying, deployment, or verifying changes

## Key facts
- Setup: pip install pyyaml && python nexus.py init && ln -sf $(pwd)/nexus.py ~/.local/bin/nexus
- Run: nexus sync --dry-run, then nexus sync after reviewing MCP commands
- Test: nexus doctor
- Lint: ruff check nexus.py (once ruff is added)

## Open next
- `CONTEXT.md#workflow`
