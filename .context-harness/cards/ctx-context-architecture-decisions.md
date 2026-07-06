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
APM to nexus migration: APM misclassified hybrid packages (superpowers' 14 skills were never deployed because APM labeled it hookpackage), created duplicate hook entries (no dedup), and couldn't declare inline MCPs. d...

## Use when
- working on architecture decisions

## Key facts
- APM to nexus migration: APM misclassified hybrid packages (superpowers' 14 skills were never deployed because APM labeled it hookpackage), created duplicate...
- Unified package model: A package can provide any combination of skills, hooks, commands, agents, and MCPs. No type classification — auto-discover via file pa...
- Inline MCP declarations: Most MCP servers are just npx <package>. Declaring them directly in the manifest eliminates the need for separate git repos.
- Hook deduplication: Hooks are deduplicated by content hash (minus metadata). Prevents the 42x duplication bug from APM.
- Security review gate: Before writing MCP configs to global IDE files, nexus shows what commands will be registered and prompts for confirmation. README/relea...

## Open next
- `CONTEXT.md#architecture-decisions`
