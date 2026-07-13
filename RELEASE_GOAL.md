# Goal: Release-Ready Agent Nexus

Make Agent Nexus release-ready as the trustworthy deployment layer for AI agent
environments. A skeptical developer should be able to see what Nexus writes,
why it is safer than ad hoc package managers, how it differs from Kasetto and
native plugin workflows, and how to verify a sync without risking local secrets
or global IDE configuration.

## Done Means

- The README no longer depends on stale negative competitor claims.
- The README has a verified target/asset matrix covering skills, hooks, MCP
  servers, commands, agents, plugins, config merge behavior, lockfile behavior,
  and supported IDE targets.
- A standalone security model explains:
  - what files Nexus reads and writes,
  - how existing MCP config keys and secrets are preserved,
  - when executable MCP/hook changes require review,
  - how hooks are deduplicated,
  - how lockfiles and cache paths make deployments traceable.
- Onboarding is release-quality:
  - either `nexus init` exists, or the manual `cp nexus.example.yml
    nexus.personal.yml` flow is clearly labeled alpha/manual,
  - quickstart includes expected output and troubleshooting,
  - no hidden dependency beyond Python 3.10+ and PyYAML.
- Demo proof exists: a transcript or artifact showing `sync`, security review,
  `doctor`, lockfile output, hook dedupe, MCP merge behavior, and Context
  Harness deployment.
- Tests cover release-critical behavior, especially target filtering,
  preserving unmanaged config, hook dedupe, and dry-run/sync safety.
- Local verification passes.

## Context To Read First

- `AGENTS.md`
- `.trellis/spec/agent-nexus/index.md`
- `PLANS.md` if present
- `FINDINGS.md`
- `EVALUATION.md`
- `README.md`
- `nexus.py`
- `nexus.example.yml`
- `tests/test_nexus.py`

## Current State

- Nexus is a real Python CLI with `sync`, `list`, `doctor`, `clean`, version
  handling, content-addressed package cache, auto-discovery, MCP merge, hook
  dedupe, lockfile output, and target deployment.
- Current public comparison language is risky because Kasetto has expanded and
  now overlaps some older claimed differentiators.
- Recent local work added package-level target filtering, including the local
  intent that Agent Reach is not deployed to Codex by Nexus.
- The Go rewrite and Homebrew/binary distribution are useful later, but not
  required for release readiness.

## Constraints And Non-Goals

- Do not rewrite Nexus in Go as part of this release unless a concrete blocker
  appears.
- Do not add Python runtime dependencies beyond PyYAML.
- Do not overwrite existing MCP configs, unmanaged hooks, secrets, or local
  personal manifest choices.
- Do not publish competitor line-item claims until current public READMEs/docs
  have been re-verified.
- Do not position Nexus as replacing native Codex/Claude/Cursor plugins. It
  should complement them as a cross-IDE environment manager.

## Milestones

1. Re-verify claims.
   Re-read current public docs for Kasetto, native Codex plugins/skills,
   Claude Code plugins/skills/hooks, and Cursor rules/MCP. Record raw external
   notes in `FINDINGS.md` and convert only verified conclusions into README.

2. Replace positioning and comparison.
   Rewrite the README opening and comparison section around verified strengths:
   one manifest, hybrid asset auto-discovery, hook lifecycle/dedupe, MCP
   security review, target-specific config merge, lockfile traceability, and
   Context Harness integration.

3. Harden safety docs and tests.
   Add or update tests for preserving unmanaged config, review gates, target
   filtering, and hook dedupe. Document security behavior in README or a
   dedicated docs file.

4. Improve onboarding and demo proof.
   Decide whether to implement `nexus init` for this release. If not, make the
   current manifest-copy flow explicit and honest. Add a demo transcript that
   shows the actual sync/doctor lifecycle.

5. Verify and close out.
   Run tests, review diffs, and update current-state docs.

## Verification

Run from `/Users/lfan/Project/agent-nexus`:

```bash
python -m pytest tests
python nexus.py doctor
```

If local deployment behavior is touched, also run the safest applicable dry run:

```bash
python nexus.py sync --dry-run
```

Manual checks:

- README comparison avoids stale "competitor lacks X" claims unless verified.
- Security model is visible before the user is asked to run `sync`.
- Quickstart describes expected output and recovery from common setup problems.
- Demo artifact proves hook dedupe and MCP review behavior.

## Loop Rules

- Continue autonomously through the next milestone when the next action is
  clear and safe.
- Ask only for human-judgment blockers, secrets, destructive operations, or
  publishing decisions.
- Keep task-local progress in Trellis task artifacts; keep long-running product
  history in `PLANS.md` and focused documentation.

## Closeout

- Update `PLANS.md` or focused product documentation with durable release
  findings, decisions, and verification.
- Update `.trellis/spec/agent-nexus/` only for reusable engineering rules or
  invariants; keep transient state in Trellis task/workspace records.
