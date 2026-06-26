# Context
<!-- context-harness:schema v3 -->

## Project
`agent-nexus` is a centralized agent environment manager that deploys skills, hooks, and MCP servers to all AI IDEs (Claude Code, Cursor, Google Antigravity) from a single `nexus.yml` manifest. The CLI (`nexus.py`) handles the full lifecycle: fetch packages from GitHub, auto-discover all asset types, deduplicate hooks, security-review MCP configs, and deploy. It replaces Microsoft's APM (buggy: hook duplication, hybrid package misclassification) and aims to surpass Kasetto (gaps: no hooks, no hybrid packages, no security gate). Tech stack: Python 3.10+ single-file CLI, PyYAML only, YAML manifests, Git shallow clones. Go rewrite (v1.0) is the next major milestone.

## Structure
```
.
nexus.py          # CLI entry point (sync, list, doctor, clean)
nexus.yml         # Central manifest (gitignored; use nexus.example.yml as template)
nexus.example.yml # Example manifest checked into repo
nexus.sh          # Legacy bash CLI (working spec for Go rewrite)
nexus.lock.yml    # Generated lockfile (resolved commits, hashes, deploy paths)
.nexus/cache/     # Content-addressed package cache (gitignored)
.github/          # GitHub Actions + global skills symlink target
```

## Rules

### Never
1. Never classify packages by type — auto-discover all assets (skills, hooks, commands, agents) from file patterns (SKILL.md, hooks.json, etc.)
2. Never write to global IDE config files without showing a security review gate first (addresses Kasetto issue #15)
3. Never add Python dependencies beyond PyYAML to `nexus.py`

### Always
1. Always deduplicate hooks by content hash before writing to any IDE config
2. Always preserve existing MCP config keys during merge — don't overwrite local configs or secrets
3. Always cache packages by commit SHA at `.nexus/cache/` (content-addressed, immutable snapshots)

### Legacy Objectives
<!-- Deprecated in schema v3. Preserve as project intent; use PLAN.md Done Criteria and Workflow Verification for active checks. -->
1. `nexus sync` exits 0 and deploys all assets from `nexus.yml` to target IDEs (`go build ./...` exits 0 once Go rewrite lands)
2. `nexus doctor` exits 0 with no health check failures
3. No duplicate hook entries in any IDE `hooks.json` after sync

## Workflow
- Setup: `pip install pyyaml && ln -sf $(pwd)/nexus.py ~/.local/bin/nexus`
- Run: `nexus sync`
- Test: `nexus doctor`
- Lint: `ruff check nexus.py` (once ruff is added)

## Language
- Manifest language: YAML, with `nexus.personal.yml` taking precedence on this machine.
- CLI implementation language: Python 3.10+ in `nexus.py`, with PyYAML as the only runtime dependency.
- Skill content language: Markdown, with each skill defined by a directory containing `SKILL.md`.

## Relationships
- `AGENTS.md` is the small activation layer; `CONTEXT.md` is the durable source of truth, indexed by `scripts/context-index.js`.
- `nexus.personal.yml` is the active local manifest; `nexus.example.yml` is the checked-in public template.
- `nexus.personal.lock.yml` records resolved package commits and deployment metadata for the personal manifest.
- `CONTEXT.md`, `NOW.md`, and `PLAN.md` are owned by context-harness; Matt Pocock engineering skills consume those docs.
- `.nexus/cache/` stores immutable package snapshots that are symlinked or deployed into target IDEs.

## Flagged Ambiguities
- The Go rewrite is planned, but the exact scaffold, package layout, and release workflow are not yet settled in this context.

## Learned Patterns
- Hook aggregation must preserve script execution paths relative to package cache dir — superpowers hooks read their own SKILL.md at runtime via relative path.
- Codex hook deployment must preserve unmanaged user hooks by only stripping commands marked with `--nexus-package`, and tests must use a temporary `CODEX_HOME` instead of the real `~/.codex` config.
- Kasetto's MCP merge preserves existing keys (no overwrite) — nexus follows the same pattern to protect local secrets.
- `~/.claude.json` is the target for user-scoped Claude Code MCP servers (not `~/.claude/.mcp.json`).
- FINDINGS.md as security boundary: external/untrusted content goes here, never into PLANS.md — prevents prompt injection via auto-read hooks.
- APM classifies hybrid packages by dominant type, missing assets — nexus always runs full auto-discovery regardless of what a package "looks like".

## Imported Agent Notes
<!-- Migrated from the pre-v3 AGENTS.md during the one-time context-harness upgrade. Keep durable facts here; keep AGENTS.md small. -->

# Agent Guide
<!-- context-harness:schema v3 -->

## Context Contract
- At session start/resume, read `NOW.md` first, then use the Context Index below to choose relevant `CONTEXT.md` sections.
- Before planning or editing, respect `CONTEXT.md` `## Rules`.
- If the user teaches a durable term, invariant, workflow, constraint, or
  correction, update `CONTEXT.md` before it scrolls away.
- Route task-local findings and decisions to `PLAN.md`; durable lessons to
  `CONTEXT.md`.
- After updating `CONTEXT.md`, run `node scripts/context-index.js update`.
- Before ending, update `NOW.md` with current focus, blockers, next step, and
  touched files.

## Project Overview
`agent-nexus` is a centralized configuration repository and framework for managing AI agent environments across multiple IDEs. It provides a single manifest that declares packages (skills, hooks, commands), MCP servers, and deployment targets — then compiles and deploys everything to Claude Code, Cursor, Google Antigravity, and Codex from one place. The project is building its own framework ("nexus") to replace Microsoft's APM, with the goal of being the best tool in this space — better than both APM and Kasetto.

## Tech Stack
- **nexus** — custom agent environment manager (manifest + CLI, replacing APM)
- **Python 3.10+** — single-file CLI (`nexus.py`), only dependency is PyYAML
- **Markdown** for skill definitions (`SKILL.md`)
- **YAML** for manifests (`nexus.example.yml`, plus gitignored personal manifests)
- **Git** for package fetching (shallow clones at pinned refs)

## Project Structure
- `nexus.example.yml`: Public template manifest checked into the repo.
- `nexus.personal.yml`: Personal manifest (gitignored). Declares packages, inline MCP servers, optional MCPs, and target IDEs for this machine.
- `nexus.example.yml`: Example manifest checked into the repo for reference.
- `nexus.py`: The nexus CLI. Symlinked to `~/.local/bin/nexus` for global access. Run `nexus sync`, `nexus list`, `nexus doctor`, `nexus clean`.
- `nexus.sh`: Legacy bash CLI (kept as backup, will be removed).
- `.nexus/`: Local cache directory (gitignored). Contains fetched packages keyed by `github.com/org/repo/commit-sha/`.

## Installed Skills & MCP Servers

### Skills (from packages)

| Package | Skill | Description |
|---------|-------|-------------|
| `lifan-builds/context-harness` | context-harness, context-init, context-launch, context-catch-up, context-maintain, context-handoff | Project context docs and context maintenance workflow skills with Codex hooks; `context-grill` is intentionally excluded in favor of Matt Pocock's `grilling` |
| `mattpocock/skills` | domain-modeling, improve-codebase-architecture, codebase-design, grill-me, grilling | Curated engineering workflow skills; latest upstream removed `zoom-out` and split reusable design/grilling helpers into separate skills |

Additional packages (like `obra/superpowers`) can be added via `nexus.personal.yml` — see `nexus.example.yml` for a public template.

## Agent skills

### Issue tracker

Issue workflow skills are not deployed right now. See `docs/agents/issue-tracker.md`.

### Triage labels

Triage labels are intentionally unconfigured while issue workflow skills are disabled. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout. Context-harness owns root `CONTEXT.md`, `NOW.md`, and `PLAN.md`; Matt Pocock's engineering skills consume those docs. See `docs/agents/domain.md`.

### MCP Servers (inline in personal manifest)

| Name | Transport | Description |
|------|-----------|-------------|
| `sequential-thinking` | stdio | Structured reasoning server |
| `playwright` | stdio | Browser automation via Playwright |
| `context7` | stdio | Up-to-date library documentation retrieval |
| `nitan-mcp` | stdio | Community MCP for Discourse integration |
| `github-mcp` (optional) | stdio | GitHub API integration (requires GITHUB_TOKEN) |

## Development Workflow
- To add a package: Add a `repo:` entry under `packages:` in `nexus.personal.yml`, then run `nexus sync`.
- To add an inline MCP: Add to the `mcps:` section of `nexus.personal.yml`. Use `optional: true` or place under `optional_mcps:` for interactive prompting.
- To add a local skill in development: Use `path: ./my-skill` under `packages:`.
- To deploy everything: Run `nexus sync` (or `nexus sync --all` to auto-include optionals).

## Coding Conventions
- Skills are directories containing a `SKILL.md` file. The directory name is the skill name.
- Hooks are discovered from `hooks/hooks.json` (Claude Code format) and `hooks/hooks-cursor.json` (Cursor format) within packages.
- The active nexus manifest is the single source of truth for all managed dependencies and MCP servers. On this machine, `nexus.personal.yml` takes precedence over `nexus.yml`.
- No package type classification — nexus auto-discovers all asset types (skills, hooks, commands, agents) from each package.

## Architecture Decisions
- **APM to nexus migration**: APM misclassified hybrid packages (superpowers' 14 skills were never deployed because APM labeled it `hook_package`), created 42 duplicate hook entries (no dedup), and couldn't declare inline MCPs. `deploy.sh` was already doing most of the real work. We're building nexus to replace both APM and deploy.sh with a unified tool.
- **Unified package model**: A package can provide any combination of skills, hooks, commands, agents, and MCPs. No type classification — auto-discover via file patterns (SKILL.md, hooks.json, etc.).
- **Inline MCP declarations**: Most MCP servers are just `npx <package>`. Declaring them directly in the manifest eliminates the need for separate git repos.
- **Hook deduplication**: Hooks are deduplicated by content hash (minus metadata). Prevents the 42x duplication bug from APM.
- **Security review gate**: Before writing MCP configs to global IDE files, nexus shows what commands will be registered and prompts for confirmation. Addresses a known Kasetto security gap (issue #15).
- **Content-addressed cache**: Packages cached by commit SHA at `.nexus/cache/github.com/org/repo/sha/`. Immutable snapshots enable instant rollbacks and safe concurrent operations.
- **Python single-file CLI**: Replaced bash+jq+inline-python with a single `nexus.py`. Only dependency is PyYAML. Eliminates ~60 subprocess spawns per sync, adds stale symlink/MCP pruning, and uses native data structures instead of JSON string concatenation.
- **Global Proxy via symlinks**: This repository is the single point-of-truth; IDE global skill directories symlink into it.
- **FINDINGS.md separation**: External/untrusted content is logged to FINDINGS.md (not PLANS.md) to prevent prompt injection via auto-read hooks.

## Context Index
