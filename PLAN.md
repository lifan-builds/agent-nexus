# Agent Nexus Release Plan

## Goal
Make Agent Nexus release-ready as the trustworthy deployment layer for AI agent
environments. A skeptical developer should be able to see what Nexus writes,
how it preserves local configuration, how it complements native tools, and how
to verify a sync before touching target IDE config.

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

## Follow-Ups
- Before publishing, switch any local-only `path: ../context-harness` release
  validation back to the public repo/ref after Context Harness is pushed.
- Keep competitor line-item claims out of launch copy unless re-verified against
  current public docs immediately before publishing.
- If commands/agents deployment becomes real instead of lockfile-only discovery,
  update README and demo docs.

## Verification
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
