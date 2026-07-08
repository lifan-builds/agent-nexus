# Agent Nexus Release Plan

## Goal
Make Agent Nexus release-ready as the trustworthy deployment layer for AI agent
environments. A skeptical developer should be able to see what Nexus writes,
how it preserves local configuration, how it complements native tools, and how
to verify a sync before touching target IDE config.

## Competitive Improvement Focus

The current public positioning should be: Agent Nexus is the safe package
manager for serious agent workspaces. It installs MCP servers, skills, hooks,
and GitHub agent packages across Claude Code, Cursor, Google Antigravity, and
Codex from one personal manifest, with dry-run review, native config sync,
lockfile traceability, and doctor verification.

AGHub and GAAL are the key competitors to keep in mind. AGHub wins on broad
22+/23-agent hub positioning and MCP/portable-skill management. GAAL wins on
polished one-YAML machine sync, `audit`/`init`/`dry-run` onboarding, repo/content
sync, and local-first trust docs. Nexus should not try to out-breadth AGHub or
out-dotfiles GAAL first; it should close the trust/onboarding gaps while owning
package-oriented safety and traceability.

Use `COMPETITIVE_IMPROVEMENT_PLAN.md` as the long-running implementation plan.
Start there when working on competitive improvements, then record task-local
progress back in this `PLAN.md`.

## Current Findings
- README and release copy now avoid stale negative competitor claims and position
  Nexus around verified behavior: one manifest, asset auto-discovery, hook
  lifecycle/dedupe, MCP review and merge, target filtering, lockfile
  traceability, skill metadata overlays, and Context Harness deployment.
- `nexus init` creates `nexus.personal.yml` from `nexus.example.yml` and refuses
  to overwrite without `--force`.
- JSON MCP merge preserves unmanaged servers, local-only keys, and existing env
  secrets when the manifest uses placeholders.
- Codex TOML MCP sync preserves existing env values inside the Nexus managed
  block when the manifest uses placeholders, while leaving content outside the
  managed block intact.
- Optional MCPs are written to the lockfile only when actually accepted for a
  sync, so skipped optional entries are not later pruned as stale Nexus-managed
  servers.
- Codex TOML MCP pruning now removes stale Nexus-managed sections from the
  managed block, matching JSON target pruning semantics.
- The public example manifest is intentionally small: Context Harness plus three
  common MCP servers. Superpowers remains a commented optional package example.

## Decisions
- Keep the Python single-file CLI for this release; the Go rewrite remains a
  later milestone.
- Do not add runtime dependencies beyond PyYAML.
- Do not position Nexus as a replacement for native Codex, Claude, Cursor, or
  Kasetto workflows. It is a repo-local cross-IDE deployment layer.
- Use `nexus.personal.yml` locally for machine-specific packages, targets, MCPs,
  and pre-release local path testing. Keep secrets out of public docs and
  examples.
- For release verification, validate the sibling local Context Harness release
  candidate with `path: ../context-harness` so `set-goal` and removed stubs are
  tested before upstream `main` is updated.

## Progress

## Follow-Ups
- Before publishing, switch any local-only `path: ../context-harness` release
  validation back to the public repo/ref after Context Harness is pushed.
- Keep competitor line-item claims out of launch copy unless re-verified against
  current public docs immediately before publishing.
- If commands/agents deployment becomes real instead of lockfile-only discovery,
  update README and demo docs.

## Verification
- `python -m pytest tests/test_nexus.py` exits 0 with 73 passed after broad target expansion and simplification review.
- `python -m py_compile nexus.py` exits 0 after broad target expansion and simplification review.
- Temp-home CLI smoke confirms omitted `targets` audit lists the four core targets and `targets: ["*"]` audit lists 41 target presets including `hermes`, `qwen-code`, and `crush`; dry-run writes no lockfile and doctor exits 0.
- `python -m pytest tests/test_nexus.py` exits 0 with 64 passed after default platform parity changes.
- `python -m py_compile nexus.py` exits 0 after default platform parity changes.
- Temp-home CLI smoke with omitted `targets` confirms `audit --json --redact-home` lists `claude`, `cursor`, `antigravity`, and `codex`; `sync --dry-run` writes no lockfile; `doctor` exits 0.
- `python -m pytest tests/test_nexus.py -k 'cli_smoke or install_local'` exits 0 with 6 passed after Phase 9 CLI smoke coverage.
- `python -m pytest tests` exits 0 with 59 passed after Phase 9 CLI smoke coverage.
- `python -m py_compile nexus.py` exits 0 after Phase 9 CLI smoke coverage.
- Markdown fence validation exits 0 after Phase 9 CLI smoke coverage.
- `python -m pytest tests/test_nexus.py -k install_local` exits 0 with 4 passed after install polish.
- `python -m pytest tests` exits 0 with 57 passed after install polish.
- `python -m py_compile nexus.py` exits 0 after install polish.
- Markdown fence validation exits 0 after install polish.
- `python -m pytest tests` exits 0 with 53 passed after adding demo proof assets.
- `python -m py_compile nexus.py` exits 0 after adding demo proof assets.
- Markdown fence validation exits 0 after adding demo proof assets.
- Example manifest YAML validation exits 0 after adding demo proof assets.
- `python -m pytest tests` exits 0 with 53 passed after hook lifecycle hardening.
- `python -m py_compile nexus.py` exits 0 after hook lifecycle hardening.
- `python nexus.py sync --dry-run` exits 0 and now prints hook command review output before deployment plan.
- Markdown fence validation exits 0 after hook docs updates.
- `python -m pytest tests` exits 0 with 52 passed after adding MCP golden-style coverage.
- `python -m py_compile nexus.py` exits 0 after adding MCP golden-style coverage.
- Markdown fence validation exits 0 after marking MCP roadmap coverage complete.
- `python -m pytest tests` exits 0 with 48 passed after enriching lockfile metadata.
- `python -m py_compile nexus.py` exits 0 after enriching lockfile metadata.
- Markdown fence validation exits 0 after lockfile docs updates.
- `python -m pytest tests` exits 0 with 47 passed after implementing `nexus audit`.
- `python -m py_compile nexus.py` exits 0 after implementing `nexus audit`.
- `python nexus.py audit --json --redact-home` exits 0 and prints redacted machine-readable inventory.
- `python nexus.py audit --target codex --redact-home` exits 0 and prints human-readable target inventory.
- Markdown fence validation exits 0 after audit docs updates.
- `python -m pytest tests` exits 0 with 41 passed after adding package trust/MCP docs.
- `python -m py_compile nexus.py` exits 0 after adding package trust/MCP docs.
- Markdown fence validation exits 0 for README, competitive roadmap, and all top-level docs files.
- `python -m pytest tests` exits 0 with 41 passed after adding docs/examples.
- `python -m py_compile nexus.py` exits 0 after adding docs/examples.
- Markdown fence validation exits 0 for README, competitive roadmap, and docs files.
- Example manifest YAML validation exits 0 for all files under `examples/*.yml`.
- Baseline `python nexus.py sync --dry-run` exits 0 and shows current package/MCP deploy plan without writing target configs.
- Baseline `python nexus.py doctor` exits 0 against the current local deployment.
- Captured CLI help for top-level, `sync`, `list`, `doctor`, `dashboard`, `clean`, `init`, and `version`.
- `python3 -m pytest -q -p no:cacheprovider tests/test_nexus.py` exits 0 with
  33 passed.
- `python3 -c "import py_compile; py_compile.compile('nexus.py', cfile='/tmp/agent-nexus-nexus.pyc', doraise=True)"`
  exits 0.
- `python3 nexus.py doctor` exits 0 against the current local deployment.
- `python3 nexus.py sync --dry-run` against the local Context Harness release
  candidate exits 0, writes no target config or lockfile, and discovers 6 Context
  Harness skills including `set-goal`.
- `python3 nexus.py sync --yes` exits 0 against the local Context Harness
  release candidate, prunes removed `context-launch`/`context-handoff`
  symlinks, deploys `set-goal`, syncs MCPs, and writes
  `nexus.personal.lock.yml`.
- After Context Harness was pushed, `python3 nexus.py sync --yes` fetched
  `lifan-builds/context-harness@main` from GitHub and deployed it locally.
- Post-sync `python3 nexus.py doctor` exits 0 with 13 Claude/Cursor/Antigravity
  skill symlinks, 12 Codex skill symlinks, 4 MCP servers on each configured
  target, and 3 Codex hook entries.
- `node scripts/context-index.js check` exits 0 after this compacted plan.

## Archive
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
- Completed competitive roadmap baseline, public docs parity, audit, MCP docs and tests, package trust docs, hook lifecycle hardening, demo assets, clone-based install polish, and subprocess CLI smoke coverage. (archived 2026-07-08)
- Added package-level `targets` and `skill_overrides`, including Codex `agents/openai.yaml` overlays materialized under `.nexus/generated/`. (archived 2026-07-08)
- Hardened JSON and Codex MCP merge/prune behavior around local keys, env placeholders, optional MCP lockfile semantics, and content outside the Codex managed block. (archived 2026-07-08)
- Made omitted manifest `targets` default to the four core native adapters (`claude`, `cursor`, `antigravity`, `codex`), added 41 skills target presets behind `targets: ["*"]`, added broad alias canonicalization, and documented the core-vs-skills target policy. (archived 2026-07-08)