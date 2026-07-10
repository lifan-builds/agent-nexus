# Now

## Current Focus
Agent Nexus browser tooling is simplified and deployed locally: Kimi WebBridge 1.11.0 is a Nexus-managed, manual-only skill on the four core targets; Playwright is optional and skipped by default; Chrome DevTools is no longer enabled as a default user MCP.

## Active Blockers
- No implementation or deployment blocker is known.
- The canonical Kimi WebBridge source is intentionally local and gitignored, so another machine needs its own adopted source until a pinned remote 1.11.0 package is available.

## Immediate Next Step
- Decide whether to publish or pin a portable Kimi WebBridge 1.11.0 package source for cross-machine reproduction.

## Session State
- Last modified: 2026-07-09
- Tracked work updates browser-tooling examples, routing documentation, Claude MCP path references, and neutral test fixtures.
- Local deployment pruned Playwright and Agent-Reach, preserved Codex-only MCPs, deployed Kimi WebBridge to Claude/Cursor/Antigravity/Codex, and removed the user Chrome DevTools MCP.
- Verification complete: `python3 -m pytest tests` (74 passed), `python3 -m py_compile nexus.py`, YAML structure checks, two reviewed dry runs, `nexus audit`, `nexus doctor`, active MCP inspection, Kimi overlay checks, and daemon health.
