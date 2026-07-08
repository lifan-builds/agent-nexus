---
id: ctx-context-learned-patterns
kind: lesson
importance: 0.78
confidence: confirmed
source: CONTEXT.md#learned-patterns
chunk: null
tokens_est: 375
tags: [context, learned-patterns, lesson]
---

# CONTEXT.md: Learned Patterns

## Summary
Hook aggregation must preserve script execution paths relative to package cache dir — superpowers hooks read their own SKILL.md at runtime via relative path.

## Use when
- avoiding repeated mistakes or applying prior corrections
- update context with durable lessons

## Key facts
- Hook aggregation must preserve script execution paths relative to package cache dir — superpowers hooks read their own SKILL.md at runtime via relative path.
- Codex hook deployment must preserve unmanaged user hooks by only stripping commands marked with --nexus-package, and tests must use a temporary CODEXHOME ins...
- Skill metadata overlays must materialize under .nexus/generated/<target>/skills/<skill>/ and target symlinks should point there; never write overlay metadata...
- Kasetto's MCP merge preserves existing keys (no overwrite) — nexus follows the same pattern to protect local secrets.
- Codex MCP pruning must edit only the Nexus managed TOML block, remove stale managed server sections listed in the previous lockfile, and preserve content out...

## Open next
- `CONTEXT.md#learned-patterns`
