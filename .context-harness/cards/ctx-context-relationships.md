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
- update context invariants

## Key facts
- AGENTS.md is the small activation layer; CONTEXT.md is the durable source of truth, indexed by scripts/context-index.js.
- nexus.personal.yml is the active local manifest; nexus.example.yml is the checked-in public template.
- nexus.personal.lock.yml records resolved package commits and deployment metadata for the personal manifest.
- CONTEXT.md, NOW.md, and PLAN.md are owned by context-harness; Matt Pocock engineering skills consume those docs.
- .nexus/cache/ stores immutable package snapshots that are symlinked or deployed into target IDEs.

## Open next
- `CONTEXT.md#relationships`
