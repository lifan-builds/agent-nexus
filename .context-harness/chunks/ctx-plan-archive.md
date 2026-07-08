# Archive

- Earlier 2026 work replaced the APM/deploy.sh workflow with Nexus, added cache
  snapshots, auto-discovery, hook dedupe, inline MCPs, lockfiles, Codex hook
  support, sparse hidden skill discovery, target filtering, and package updates.
- Historical deployment notes mention old Context Harness skills such as
  `context-launch`, `context-handoff`, and `context-grill`; those are superseded
  by the current release path, which deploys `set-goal` and prunes removed stubs.
- The Go rewrite, `nexus add`, `nexus update`, shell completions, and binary
  distribution remain future work, not release blockers for the Python CLI.

- Completed competitive roadmap Phase 0 baseline: read required context/code/docs, captured CLI help, checked gitignored local-only files, and ran baseline verification. (archived 2026-07-07)
- Added public docs for target/resource support, manifest fields, package behavior, and honest comparison positioning. (archived 2026-07-07)
- Added copyable example manifests for minimal, Context Harness, MCP-only, team, and package-overlay setups. (archived 2026-07-07)
- Linked the new docs and examples from README so the top-level public entry point points to deeper references. (archived 2026-07-07)
- Added `docs/package-trust.md` to explain package sources, refs, pinning, discovery safety, executable surfaces, dry-run review, lockfile traceability, and planned inspection commands. (archived 2026-07-07)
- Added `docs/mcp.md` to document stdio/SSE/HTTP MCP schema, per-target output formats, merge preservation, managed/unmanaged semantics, Codex managed TOML blocks, and stale pruning. (archived 2026-07-07)
- Added `nexus audit` read-only discovery with human/JSON output, target filtering, home-path redaction, MCP env/header redaction, skill stale-symlink detection, and hook managed/unmanaged counts. (archived 2026-07-07)
- Updated README, security model, target matrix, and demo transcript so audit is the first trust-building step. (archived 2026-07-07)
- Enriched lockfile metadata with manifest path, package source metadata, GitHub source URL/ref/commit/cache details, local path details, hook deployment targets, and floating-ref warnings. (archived 2026-07-07)
- Added MCP golden-style coverage for empty JSON config creation, managed stdio updates, unmanaged/local key preservation, stale managed pruning, skipped optional preservation, Codex outside-block preservation, and JSON formatting behavior. (archived 2026-07-07)
- Added hook security review output in dry-run/interactive sync, `docs/hooks.md`, and Cursor/Codex hook lifecycle tests covering command visibility, dedupe, unmanaged preservation, and stale managed pruning. (archived 2026-07-07)
- Added Phase 6 demo proof assets: `docs/demo-before-after.md`, `docs/demo-recording.md`, `docs/screenshot-checklist.md`, and README links to the demo materials. (archived 2026-07-07)
- Completed Phase 7 clone-based install polish: README now recommends `scripts/install-local.sh`, and the installer refuses to replace unrelated `nexus` commands unless forced, supports safe uninstall, and has focused tests. (archived 2026-07-07)
- Added Phase 9 subprocess CLI smoke coverage for `init`, `audit --json --redact-home`, `sync --dry-run`, `doctor`, and `init` overwrite errors using temporary `HOME` and `CODEX_HOME`. (archived 2026-07-07)
- Made omitted manifest `targets` default to all implemented adapters (`claude`, `cursor`, `antigravity`, `codex`), added target alias canonicalization, and documented the platform-default policy without claiming unimplemented adapters. (archived 2026-07-07)
- Added `RELEASE_GOAL.md` for Agent Nexus release readiness. (archived 2026-07-07)
- Replaced stale README competitor comparison with verified positioning and (archived 2026-07-07)
- Added `nexus init` and troubleshooting. (archived 2026-07-07)
- Added `docs/security-model.md` and `docs/demo-transcript.md`. (archived 2026-07-07)
- Added package-level `targets` and `skill_overrides`, including Codex (archived 2026-07-07)
- Hardened JSON and Codex MCP merge behavior around local keys and env (archived 2026-07-07)
- Fixed optional MCP lockfile semantics. (archived 2026-07-07)
- Fixed Codex TOML stale MCP pruning and added regression coverage. (archived 2026-07-07)
- Updated the local gitignored manifest to test `../context-harness`, include (archived 2026-07-07)
