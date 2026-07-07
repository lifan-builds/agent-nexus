# Now

## Current Focus
Agent Nexus competitive roadmap work is in progress. Phase 0 baseline is complete. Phase 1 public docs parity is in place. Phase 2 `nexus audit` read-only discovery is implemented and documented. Phase 3 MCP docs and golden-style coverage are in place. Phase 4 trust docs cover package trust/lockfile traceability, and lockfile metadata now records richer package provenance. Phase 5 hook lifecycle hardening is documented and tested with hook command review output. Phase 6 demo/example assets are in place. Phase 7 clone-based install polish is complete with a safer reversible `scripts/install-local.sh` path.

## Active Blockers
- No implementation blocker is known.
- Competitive claims about AGHub/GAAL should be re-verified before publishing comparison copy externally.

## Immediate Next Step
- Continue `COMPETITIVE_IMPROVEMENT_PLAN.md` with the next highest-value gap: CI/release quality from Phase 9, launch-ready story cleanup from Phase 10, or target expansion strategy only if supported by real adapter work.

## Session State
- Last modified: 2026-07-07
- Files touched: `README.md`, `PLAN.md`, `NOW.md`, `COMPETITIVE_IMPROVEMENT_PLAN.md`, `docs/targets.md`, `docs/manifest.md`, `docs/packages.md`, `docs/package-trust.md`, `docs/mcp.md`, `docs/hooks.md`, `docs/comparison.md`, `docs/security-model.md`, `docs/demo-transcript.md`, `docs/demo-before-after.md`, `docs/demo-recording.md`, `docs/screenshot-checklist.md`, `examples/*.yml`, `scripts/install-local.sh`, `nexus.py`, `tests/test_nexus.py`.
- Verification complete: tests, py_compile, audit JSON/text smoke checks, sync dry-run smoke checks, markdown fence validation, example YAML validation, lockfile metadata tests, MCP golden-style tests, hook lifecycle tests, demo docs checks, and installer safety tests passed after the latest updates.
