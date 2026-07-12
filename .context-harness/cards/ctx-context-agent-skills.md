---
id: ctx-context-agent-skills
kind: context
importance: 0.65
confidence: confirmed
source: CONTEXT.md#agent-skills
chunk: null
tokens_est: 225
tags: [context, agent-skills, issue-tracker, triage-labels, domain-docs, mcp-servers-inline-in-personal-manifest]
---

# CONTEXT.md: Agent skills

## Summary
Issue workflow skills are not deployed right now. See docs/agents/issue-tracker.md.

## Use when
- working on agent skills, issue tracker, triage labels

## Key facts
- Triage labels are intentionally unconfigured while issue workflow skills are disabled. See docs/agents/triage-labels.md.
- Single-context layout. Context-harness owns root CONTEXT.md, NOW.md, and PLAN.md; Matt Pocock's engineering skills consume those docs.
- | Name | Transport | Description | |------|-----------|-------------| | sequential-thinking | stdio | Structured reasoning server | | playwright | stdio |...

## Retrieval order
- Read `NOW.md` and concise `CONTEXT.md` as the always-read layer.
- Use this card before opening bulky `PLAN.md`, chunks, or raw source sections for this topic.
- Open raw detail only when this summary is insufficient for the task.

## Open next only if needed
- `CONTEXT.md#agent-skills`
