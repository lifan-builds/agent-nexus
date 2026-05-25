# Agent Guide
<!-- context-harness:schema v2 -->

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
| `fantasy-cc/context-harness` | context-harness | Project docs generation (AGENTS.md, PLANS.md, FINDINGS.md, EVALUATION.md, README.md) with auto-recovery hooks |
| `mattpocock/skills` | setup-matt-pocock-skills, diagnose, tdd, zoom-out, improve-codebase-architecture, grill-with-docs | Curated engineering workflow skills that consume context-harness docs |

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
<!-- context-harness:index:start -->
Generated from `CONTEXT.md` by `node scripts/context-index.js update`.
Use this index to open only the `CONTEXT.md` sections relevant to the task.

- `NOW.md` - current focus, blockers, and next step. Read first on start/resume.
- `CONTEXT.md#project` - project identity and purpose.
- `CONTEXT.md#structure` - repo map and important directories.
- `CONTEXT.md#rules` - hard constraints, habits, and objectives. Subsections: Never, Always, Objectives.
- `CONTEXT.md#workflow` - setup, run, test, lint, and deploy commands.
- `CONTEXT.md#language` - canonical terms and avoided names.
- `CONTEXT.md#relationships` - durable invariants and domain relationships.
- `CONTEXT.md#flagged-ambiguities` - resolved naming or meaning conflicts.
- `CONTEXT.md#learned-patterns` - durable lessons from corrections or failed attempts.
<!-- context-harness:index:end -->
