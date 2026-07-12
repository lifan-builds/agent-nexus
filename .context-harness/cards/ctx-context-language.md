---
id: ctx-context-language
kind: language
importance: 0.82
confidence: confirmed
source: CONTEXT.md#language
chunk: null
tokens_est: 72
tags: [context, language]
---

# CONTEXT.md: Language

## Summary
Manifest language: YAML, with nexus.personal.yml taking precedence on this machine.

## Use when
- using canonical project terms or resolving naming ambiguity

## Key facts
- CLI implementation language: Python 3.10+ in nexus.py, with PyYAML as the only runtime dependency.
- Skill content language: Markdown, with each skill defined by a directory containing SKILL.md.

## Retrieval order
- Read `NOW.md` and concise `CONTEXT.md` as the always-read layer.
- Use this card before opening bulky `PLAN.md`, chunks, or raw source sections for this topic.
- Open raw detail only when this summary is insufficient for the task.

## Open next only if needed
- `CONTEXT.md#language`
