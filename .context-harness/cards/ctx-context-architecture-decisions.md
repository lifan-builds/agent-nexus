---
id: ctx-context-architecture-decisions
kind: context
importance: 0.65
confidence: confirmed
source: CONTEXT.md#architecture-decisions
chunk: null
tokens_est: 450
tags: [context, architecture-decisions]
---

# CONTEXT.md: Architecture Decisions

## Summary
APM to nexus migration: APM misclassified hybrid packages (superpowers' 14 skills were never deployed because APM labeled it hookpackage), created duplicate hook entries (no dedup), and couldn't declare inline MCPs.

## Use when
- working on architecture decisions

## Key facts
- Unified package model: A package can provide any combination of skills, hooks, commands, agents, and MCPs.
- Inline MCP declarations: Most MCP servers are just npx <package>. Declaring them directly in the manifest eliminates the need for separate git repos.
- Hook deduplication: Hooks are deduplicated by content hash (minus metadata). Prevents the 42x duplication bug from APM.
- Security review gate: Before writing MCP configs to global IDE files, nexus shows what commands will be registered and prompts for confirmation.
- Content-addressed cache: Packages cached by commit SHA at .nexus/cache/github.com/org/repo/sha/.

## Retrieval order
- Read `NOW.md` and concise `CONTEXT.md` as the always-read layer.
- Use this card before opening bulky `PLAN.md`, chunks, or raw source sections for this topic.
- Open raw detail only when this summary is insufficient for the task.

## Open next only if needed
- `CONTEXT.md#architecture-decisions`
