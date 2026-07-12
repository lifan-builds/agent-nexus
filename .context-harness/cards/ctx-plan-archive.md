---
id: ctx-plan-archive
kind: plan
importance: 0.85
confidence: confirmed
source: PLAN.md#archive
chunk: .context-harness/chunks/ctx-plan-archive.md
tokens_est: 1308
tags: [plan, archive]
---

# PLAN.md: Archive

## Summary
Earlier 2026 work replaced the APM/deploy.sh workflow with Nexus, added cache snapshots, auto-discovery, hook dedupe, inline MCPs, lockfiles, Codex hook support, sparse hidden skill discovery, target filtering,...

## Use when
- continuing task-local archive

## Key facts
- Historical deployment notes mention old Context Harness skills such as context-launch, context-handoff, and context-grill;...
- The Go rewrite, nexus add, nexus update, shell completions, and binary distribution remain future work, not release blockers for the Python CLI.
- Completed competitive roadmap Phase 0 baseline: read required context/code/docs, captured CLI help, checked gitignored local-only files,...
- Added public docs for target/resource support, manifest fields, package behavior, and honest comparison positioning. (archived 2026-07-07)
- Added copyable example manifests for minimal, Context Harness, MCP-only, team, and package-overlay setups. (archived 2026-07-07)

## Retrieval order
- Read `NOW.md` and concise `CONTEXT.md` as the always-read layer.
- Use this card before opening bulky `PLAN.md`, chunks, or raw source sections for this topic.
- Open raw detail only when this summary is insufficient for the task.

## Open next only if needed
- `PLAN.md#archive`
- `.context-harness/chunks/ctx-plan-archive.md`
