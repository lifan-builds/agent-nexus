---
id: ctx-context-operating-constraints
kind: constraints
importance: 0.9
confidence: confirmed
source: CONTEXT.md#operating-constraints
chunk: null
tokens_est: 200
tags: [context, operating-constraints, constraints]
---

# CONTEXT.md: Operating Constraints

## Summary
Do not classify packages by type — auto-discover all assets (skills, hooks, commands, agents) from file patterns (SKILL.md, hooks.json, etc.).

## Use when
- before choosing an implementation or changing project behavior

## Key facts
- Do not write to global IDE config files without showing a security review gate first.
- Do not add Python dependencies beyond PyYAML to nexus.py.
- Deduplicate hooks by content hash before writing to any IDE config.
- Preserve existing MCP config keys during merge — don't overwrite local configs or secrets.
- Cache packages by commit SHA at .nexus/cache/ (content-addressed, immutable snapshots).

## Retrieval order
- Read `NOW.md` and concise `CONTEXT.md` as the always-read layer.
- Use this card before opening bulky `PLAN.md`, chunks, or raw source sections for this topic.
- Open raw detail only when this summary is insufficient for the task.

## Open next only if needed
- `CONTEXT.md#operating-constraints`
