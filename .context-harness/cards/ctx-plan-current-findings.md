---
id: ctx-plan-current-findings
kind: plan
importance: 0.85
confidence: confirmed
source: PLAN.md#current-findings
chunk: null
tokens_est: 296
tags: [plan, current-findings]
---

# PLAN.md: Current Findings

## Summary
README and release copy now avoid stale negative competitor claims and position Nexus around verified behavior: one manifest, asset auto-discovery, hook lifecycle/dedupe, MCP review and merge, target filtering,...

## Use when
- continuing task-local current findings

## Key facts
- nexus init creates nexus.personal.yml from nexus.example.yml and refuses to overwrite without --force.
- JSON MCP merge preserves unmanaged servers, local-only keys, and existing env secrets when the manifest uses placeholders.
- Codex TOML MCP sync preserves existing env values inside the Nexus managed block when the manifest uses placeholders,...
- Optional MCPs are written to the lockfile only when actually accepted for a sync, so skipped optional entries are not later pruned as stale Nexus-managed...
- Codex TOML MCP pruning now removes stale Nexus-managed sections from the managed block, matching JSON target pruning semantics.

## Retrieval order
- Read `NOW.md` and concise `CONTEXT.md` as the always-read layer.
- Use this card before opening bulky `PLAN.md`, chunks, or raw source sections for this topic.
- Open raw detail only when this summary is insufficient for the task.

## Open next only if needed
- `PLAN.md#current-findings`
