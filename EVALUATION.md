# Evaluation & Contracts

This document contains objective grading criteria and specific verification contracts for tasks defined in `PLANS.md`.

## Grading Criteria
- **Functionality**: Must seamlessly manage skills, hooks, and MCP servers across all target IDEs. Packages must be fully auto-discovered (no manual type classification).
- **Code Quality**: Clean manifest schema, no orphaned artifacts, no duplicate entries. Nexus CLI must have zero Python/Node runtime deps.
- **Testing**: Verified by running `nexus sync` and confirming all IDEs recognize installed skills, hooks are deduplicated, and MCP configs are correct.

## Active Sprint Contracts

### [Nexus v0.1 — Manifest + Documentation]
- **Verification Method**: `nexus.yml` passes YAML validation (`yq . nexus.yml`); all project docs reference nexus (not APM); `.gitignore` covers `.nexus/`.
- **Acceptance Threshold**: No references to APM in tracked files (except historical entries in PLANS.md/FINDINGS.md). `nexus.yml` contains all dependencies from the old `apm.yml`.

### [Nexus v0.2 — CLI Implementation]
- **Verification Method**: Run `nexus sync` and verify: (1) packages fetched to `.nexus/cache/`, (2) skills symlinked to `~/.claude/skills/`, `~/.cursor/skills/`, `~/.gemini/antigravity/skills/`, (3) MCP configs merged into all target IDE config files, (4) hooks aggregated and deduplicated, (5) `nexus.lock.yml` generated with deployment paths. Compare output against current `deploy.sh` for parity.
- **Acceptance Threshold**: `nexus sync` produces identical functional output to `deploy.sh` for skills and MCPs. Hook entries reduced from 84 to 2 in `.cursor/hooks.json`. Security review gate displays changes before writing.

## Evaluation Log
- [2026-03-26] - [Extract Context-Harness to GitHub] - [Grade: Pass] - [Skill successfully extracted to separate Git repo, published, and linked via APM.]
- [2026-04-12] - [Nexus v0.1 — Manifest + Documentation] - [Grade: Pass] - [nexus.yml created with all deps migrated. All 5 project docs updated. APM artifacts removed. .gitignore updated.]
