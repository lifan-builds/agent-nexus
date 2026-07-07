# Progress

- [x] Completed competitive roadmap Phase 0 baseline: read required context/code/docs, captured CLI help, checked gitignored local-only files, and ran baseline verification.
- [x] Added public docs for target/resource support, manifest fields, package behavior, and honest comparison positioning.
- [x] Added copyable example manifests for minimal, Context Harness, MCP-only, team, and package-overlay setups.
- [x] Linked the new docs and examples from README so the top-level public entry point points to deeper references.
- [x] Added `docs/package-trust.md` to explain package sources, refs, pinning, discovery safety, executable surfaces, dry-run review, lockfile traceability, and planned inspection commands.
- [x] Added `docs/mcp.md` to document stdio/SSE/HTTP MCP schema, per-target output formats, merge preservation, managed/unmanaged semantics, Codex managed TOML blocks, and stale pruning.
- [x] Added `nexus audit` read-only discovery with human/JSON output, target filtering, home-path redaction, MCP env/header redaction, skill stale-symlink detection, and hook managed/unmanaged counts.
- [x] Updated README, security model, target matrix, and demo transcript so audit is the first trust-building step.
- [x] Enriched lockfile metadata with manifest path, package source metadata, GitHub source URL/ref/commit/cache details, local path details, hook deployment targets, and floating-ref warnings.
- [x] Added MCP golden-style coverage for empty JSON config creation, managed stdio updates, unmanaged/local key preservation, stale managed pruning, skipped optional preservation, Codex outside-block preservation, and JSON formatting behavior.
- [x] Added hook security review output in dry-run/interactive sync, `docs/hooks.md`, and Cursor/Codex hook lifecycle tests covering command visibility, dedupe, unmanaged preservation, and stale managed pruning.
- [x] Added Phase 6 demo proof assets: `docs/demo-before-after.md`, `docs/demo-recording.md`, `docs/screenshot-checklist.md`, and README links to the demo materials.
- [x] Completed Phase 7 clone-based install polish: README now recommends `scripts/install-local.sh`, and the installer refuses to replace unrelated `nexus` commands unless forced, supports safe uninstall, and has focused tests.
- [x] Added `RELEASE_GOAL.md` for Agent Nexus release readiness.
- [x] Replaced stale README competitor comparison with verified positioning and
  a target/asset matrix.
- [x] Added `nexus init` and troubleshooting.
- [x] Added `docs/security-model.md` and `docs/demo-transcript.md`.
- [x] Added package-level `targets` and `skill_overrides`, including Codex
  `agents/openai.yaml` overlays materialized under `.nexus/generated/`.
- [x] Hardened JSON and Codex MCP merge behavior around local keys and env
  placeholders.
- [x] Fixed optional MCP lockfile semantics.
- [x] Fixed Codex TOML stale MCP pruning and added regression coverage.
- [x] Updated the local gitignored manifest to test `../context-harness`, include
  `set-goal`, and stop requesting removed Context Harness stubs.
