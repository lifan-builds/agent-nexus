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
- avoiding a repeated failure or applying a durable correction

## Key facts
- Codex hook deployment must preserve unmanaged user hooks by only stripping commands marked with --nexus-package,...
- Skill metadata overlays must materialize under .nexus/generated/<target>/skills/<skill>/ and target symlinks should point there;...
- Kasetto's MCP merge preserves existing keys (no overwrite) — nexus follows the same pattern to protect local secrets.
- Codex MCP pruning must edit only the Nexus managed TOML block, remove stale managed server sections listed in the previous lockfile,...
- Omitted manifest targets default to the four core native adapters (claude, cursor, antigravity, codex); targets: [""] expands to all skills target presets,...

## Retrieval order
- Read `NOW.md` and concise `CONTEXT.md` as the always-read layer.
- Use this card before opening bulky `PLAN.md`, chunks, or raw source sections for this topic.
- Open raw detail only when this summary is insufficient for the task.

## Open next only if needed
- `CONTEXT.md#learned-patterns`
