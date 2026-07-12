---
id: ctx-context-development-workflow
kind: workflow
importance: 0.65
confidence: confirmed
source: CONTEXT.md#development-workflow
chunk: null
tokens_est: 109
tags: [context, development-workflow, workflow]
---

# CONTEXT.md: Development Workflow

## Summary
To add a package: Add a repo: entry under packages: in nexus.personal.yml, then run nexus sync.

## Use when
- working on development workflow

## Key facts
- To add an inline MCP: Add to the mcps: section of nexus.personal.yml. Use optional: true or place under optionalmcps: for interactive prompting.
- To add a local skill in development: Use path: ./my-skill under packages:.
- To deploy everything: Run nexus sync (or nexus sync --all to auto-include optionals).

## Retrieval order
- Read `NOW.md` and concise `CONTEXT.md` as the always-read layer.
- Use this card before opening bulky `PLAN.md`, chunks, or raw source sections for this topic.
- Open raw detail only when this summary is insufficient for the task.

## Open next only if needed
- `CONTEXT.md#development-workflow`
