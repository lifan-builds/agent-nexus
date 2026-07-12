---
id: ctx-context-relationships
kind: invariant
importance: 0.82
confidence: confirmed
source: CONTEXT.md#relationships
chunk: null
tokens_est: 143
tags: [context, relationships, invariant]
---

# CONTEXT.md: Relationships

## Summary
AGENTS.md is the small activation layer; CONTEXT.md is the durable source of truth, indexed by scripts/context-index.js.

## Use when
- changing architecture or domain relationships

## Key facts
- nexus.personal.yml is the active local manifest; nexus.example.yml is the checked-in public template.
- nexus.personal.lock.yml records resolved package commits and deployment metadata for the personal manifest.
- CONTEXT.md, NOW.md, and PLAN.md are owned by context-harness; Matt Pocock engineering skills consume those docs.
- .nexus/cache/ stores immutable package snapshots that are symlinked or deployed into target IDEs.

## Retrieval order
- Read `NOW.md` and concise `CONTEXT.md` as the always-read layer.
- Use this card before opening bulky `PLAN.md`, chunks, or raw source sections for this topic.
- Open raw detail only when this summary is insufficient for the task.

## Open next only if needed
- `CONTEXT.md#relationships`
