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
- To add a package: Add a repo: entry under packages: in nexus.personal.yml, then run nexus sync.
- To add an inline MCP: Add to the mcps: section of nexus.personal.yml. Use optional: true or place under optionalmcps: for interactive prompting.
- To add a local skill in development: Use path: ./my-skill under packages:.
- To deploy everything: Run nexus sync (or nexus sync --all to auto-include optionals).

## Open next
- `CONTEXT.md#development-workflow`
