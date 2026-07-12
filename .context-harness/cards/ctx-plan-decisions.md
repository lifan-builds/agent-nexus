---
id: ctx-plan-decisions
kind: plan
importance: 0.85
confidence: confirmed
source: PLAN.md#decisions
chunk: null
tokens_est: 165
tags: [plan, decisions]
---

# PLAN.md: Decisions

## Summary
Keep the Python single-file CLI for this release; the Go rewrite remains a later milestone.

## Use when
- continuing task-local decisions

## Key facts
- Do not add runtime dependencies beyond PyYAML.
- Do not position Nexus as a replacement for native Codex, Claude, Cursor, or Kasetto workflows. It is a repo-local cross-IDE deployment layer.
- Use nexus.personal.yml locally for machine-specific packages, targets, MCPs, and pre-release local path testing. Keep secrets out of public docs and examples.
- For release verification, validate the sibling local Context Harness release candidate with path:...

## Retrieval order
- Read `NOW.md` and concise `CONTEXT.md` as the always-read layer.
- Use this card before opening bulky `PLAN.md`, chunks, or raw source sections for this topic.
- Open raw detail only when this summary is insufficient for the task.

## Open next only if needed
- `PLAN.md#decisions`
