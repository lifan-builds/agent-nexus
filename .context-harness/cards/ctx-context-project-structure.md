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
- nexus.example.yml: Public template manifest checked into the repo.
- nexus.personal.yml: Personal manifest (gitignored). Declares packages, inline MCP servers, optional MCPs, and target IDEs for this machine.
- nexus.example.yml: Example manifest checked into the repo for reference.
- nexus.py: The nexus CLI. Symlinked to ~/.local/bin/nexus for global access. Run nexus sync, nexus list, nexus doctor, nexus clean.
- nexus.sh: Legacy bash CLI (kept as backup, will be removed).

## Open next
- `CONTEXT.md#project-structure`
