---
id: ctx-context-coding-conventions
kind: context
importance: 0.65
confidence: confirmed
source: CONTEXT.md#coding-conventions
chunk: null
tokens_est: 132
tags: [context, coding-conventions]
---

# CONTEXT.md: Coding Conventions

## Summary
Skills are directories containing a SKILL.md file. The directory name is the skill name.

## Use when
- working on coding conventions

## Key facts
- Hooks are discovered from hooks/hooks.json (Claude Code format) and hooks/hooks-cursor.json (Cursor format) within packages.
- The active nexus manifest is the single source of truth for all managed dependencies and MCP servers.
- No package type classification — nexus auto-discovers all asset types (skills, hooks, commands, agents) from each package.

## Retrieval order
- Read `NOW.md` and concise `CONTEXT.md` as the always-read layer.
- Use this card before opening bulky `PLAN.md`, chunks, or raw source sections for this topic.
- Open raw detail only when this summary is insufficient for the task.

## Open next only if needed
- `CONTEXT.md#coding-conventions`
