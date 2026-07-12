---
id: ctx-context-tech-stack
kind: context
importance: 0.65
confidence: confirmed
source: CONTEXT.md#tech-stack
chunk: null
tokens_est: 88
tags: [context, tech-stack]
---

# CONTEXT.md: Tech Stack

## Summary
nexus — custom agent environment manager (manifest + CLI, replacing APM)

## Use when
- working on tech stack

## Key facts
- Python 3.10+ — single-file CLI (nexus.py), only dependency is PyYAML
- Markdown for skill definitions (SKILL.md)
- YAML for manifests (nexus.example.yml, plus gitignored personal manifests)
- Git for package fetching (shallow clones at pinned refs)

## Retrieval order
- Read `NOW.md` and concise `CONTEXT.md` as the always-read layer.
- Use this card before opening bulky `PLAN.md`, chunks, or raw source sections for this topic.
- Open raw detail only when this summary is insufficient for the task.

## Open next only if needed
- `CONTEXT.md#tech-stack`
