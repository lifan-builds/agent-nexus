# agent-nexus — Nexus Framework v0.1

This is a living document. Keep Progress, Surprises & Discoveries,
Decision Log, and Outcomes & Retrospective up to date as work proceeds.

## Handoff (session state)

- **Last updated:** 2026-04-12
- **Focus:** Nexus framework v0.1 complete. CLI implemented and validated. Phase 3 (polish) is next.
- **Done:** `nexus.yml` manifest created; `nexus.sh` CLI implemented (sync, list, doctor, clean); 15 skills deployed (including all 14 superpowers skills that APM missed); hooks deduplicated from 84 to 1; MCP configs synced to 3 IDEs; lockfile generated.
- **Open:** Remove `deploy.sh`. Add `nexus init`, `nexus add`, `nexus update`. Consider Rust/Go rewrite.

## Purpose / Big Picture
Build a best-in-class agent environment manager ("nexus") that deploys skills, hooks, and MCP servers to all AI IDEs from a single manifest. Replace Microsoft's APM (buggy, limited) and surpass Kasetto (no hooks, no hybrid packages, no security gates) with a framework that handles the full lifecycle: fetch, auto-discover, compile, review, deploy, and clean.

## Progress

### Phase 0: Bootstrap (completed)
- [x] Initial legacy `install.sh` removal
- [x] APM initialization and `apm.yml` configuration
- [x] First `apm install` and lockfile generation
- [x] Creation of symlink commands for global IDE hookups
- [x] Run `context-harness` to bootstrap project docs
- [x] Enhanced `context-harness` with FINDINGS.md, auto-recovery hooks
- [x] Replaced puppeteer MCP with playwright MCP server
- [x] Installed `obra/superpowers` via APM
- [x] Extracted `context-harness` to GitHub (`fantasy-cc/context-harness`)
- [x] Cursor MCP merge into `~/.cursor/mcp.json`
- [x] Fixed Antigravity MCP loading (npx path resolution)

### Phase 1: Nexus design + manifest + docs (current)
- [x] (2026-04-12) Research Kasetto — identified gaps: no hooks, no hybrid packages, no inline MCPs, no security review, security issue #15
- [x] (2026-04-12) Research ecosystem — APM, Kasetto, skills CLI, killer-skills compared
- [x] (2026-04-12) Documented APM bugs — 42x hook duplication, hybrid package misclassification (superpowers skills never deployed)
- [x] (2026-04-12) Designed nexus.yml manifest schema
- [x] (2026-04-12) Created `nexus.yml` with all deps migrated from `apm.yml`
- [x] (2026-04-12) Updated all project docs (AGENTS.md, PLANS.md, FINDINGS.md, EVALUATION.md, README.md)
- [x] (2026-04-12) Removed APM artifacts (`apm.yml`, `apm.lock.yaml`)
- [x] (2026-04-12) Updated `.gitignore` for nexus

### Phase 2: Nexus CLI implementation (complete)
- [x] (2026-04-12) Implement `nexus sync` — fetch packages, auto-discover assets, compile skills, merge MCPs, aggregate+dedup hooks, security review gate
- [x] (2026-04-12) Implement `nexus list` — show installed packages, skills, MCPs
- [x] (2026-04-12) Implement `nexus doctor` — health checks (symlinks, MCP configs, hook dedup, lockfile consistency)
- [x] (2026-04-12) Implement `nexus clean` — remove all tracked artifacts using lockfile
- [x] (2026-04-12) Generate `nexus.lock.yml` with resolved commits, content hashes, and deployment paths
- [x] (2026-04-12) Validated: 15 skills deployed (vs 1 with APM), hooks deduplicated 84->1, MCPs synced to 3 IDEs
- [x] (2026-04-12) Removed `deploy.sh` — nexus sync validated end-to-end
- [x] (2026-04-12) Fixed broken Cursor skill symlink (stale `project-context` from old repo)
- [x] (2026-04-12) Added `nexus` to PATH via `~/.local/bin/nexus` symlink

### Phase 3: Go rewrite + distribution
- [ ] Rewrite `nexus.sh` in Go as `nexus` single binary
- [ ] Port: YAML/JSON parsing (encoding/json, gopkg.in/yaml.v3)
- [ ] Port: git operations (go-git or shelling out to git)
- [ ] Port: all 4 subcommands (sync, list, doctor, clean)
- [ ] Add: `nexus init` — generate nexus.yml from scratch or migrate from apm.yml
- [ ] Add: `nexus add <repo>` — add a package interactively
- [ ] Add: `nexus update [package]` — bump to latest ref
- [ ] Shell completions (cobra generates bash, zsh, fish, powershell)
- [ ] Cross-compile for macOS (arm64, amd64), Linux (amd64)
- [ ] GitHub releases + `brew install`

## Surprises & Discoveries
- APM does not inherently contain an `antigravity` compilation target; we route Google Antigravity to `.github/skills` via symlinks.
- APM and the skills CLI coexist without conflict — different deploy paths.
- Hooks defined in SKILL.md YAML frontmatter are auto-executed by Claude Code without separate settings.json configuration.
- APM creates 42 duplicate hook entries in `.cursor/hooks.json` — no deduplication logic exists.
- APM classifies `obra/superpowers` as `hook_package` only, missing 14 skills, 3 commands, and 1 agent definition.
- Kasetto (the closest competitor) explicitly lists "hooks management" and "agent config management" as unimplemented roadmap items — these are our key differentiators.
- Kasetto has a security issue (#15): untrusted repos can become executable MCP config without approval gates.

## Decision Log
- **Adopted APM over Bash Scripts** (2026-03): Removed `install.sh` to leverage APM for declarative dependency management.
- **Adopted Symlink Strategy** (2026-03): Symlink global IDE skill dirs into this repo for zero-config setup.
- **Dual Package Manager** (2026-03): APM for structured skills; skills CLI for vercel-labs ecosystem.
- **Puppeteer to Playwright** (2026-03): Switched to Anthropic's official playwright MCP server.
- **FINDINGS.md as security boundary** (2026-03): External content separated from PLANS.md to prevent prompt injection.
- **APM to nexus migration** (2026-04-12): APM's bugs (hook duplication, hybrid package misclassification) and limitations (no inline MCPs, no security review) made it a liability. deploy.sh was already doing most of the work. Building nexus as a unified replacement that also surpasses Kasetto.
- **Unified package model** (2026-04-12): Eliminated package type classification. Auto-discover all asset types via file patterns. A package can provide skills + hooks + commands + agents + MCPs.
- **Security review gate** (2026-04-12): Show MCP commands before writing to global config. Addresses Kasetto's security gap.
- **Shell prototype, Go for v1.0** (2026-04-12): Bash script for rapid prototyping and design iteration. Go chosen over Rust for v1.0 rewrite because: single static binary like Rust, much faster to write (no borrow checker), go-git for native git ops, built-in YAML/JSON, easy cross-compilation. Shell stays as the working spec.

## Outcomes & Retrospective

### Phase 0 (Bootstrap) — Complete
The APM-based architecture successfully replaced handwritten copying scripts. Deployed 3 skills and 6+ MCP servers across Claude Code, Cursor, and Antigravity. However, APM proved to be a bottleneck: hybrid packages weren't fully deployed, hooks accumulated duplicates, and `deploy.sh` grew to 530 lines compensating for APM's limitations.

### Phase 1 (Nexus Design) — Complete
Researched the ecosystem (Kasetto, APM, skills CLI, killer-skills). Identified Kasetto's gaps and APM's bugs. Designed `nexus.yml` manifest with unified package model, inline MCP declarations, and optional dependency support. Migrated all configuration and updated all project documentation.

### Phase 2 (CLI Implementation) — Complete
Implemented `nexus.sh` with all 4 subcommands (sync, list, doctor, clean). Key results: 15 skills deployed (vs 1 with APM), hooks deduplicated from 84 to 1, MCP configs synced to 3 IDEs, lockfile generated with full discovery metadata. Security review gate shows MCP commands before writing. Removed `deploy.sh`. Added `nexus` to global PATH.

## Context and Orientation
The repository contains `nexus.yml` as the central manifest (gitignored; use `nexus.example.yml` as template) and `nexus.sh` as the CLI entry point. The `.nexus/` directory (gitignored) holds the package cache and compiled artifacts. Skills are also installed globally via the skills CLI (`~/.agents/skills/`). The context-harness skill maintains five documents (AGENTS.md, PLANS.md, FINDINGS.md, EVALUATION.md, README.md).

## Validation and Acceptance
- `nexus.yml` is valid YAML and contains all dependencies from the old `apm.yml`
- `nexus sync` fetches packages, auto-discovers all assets (skills, hooks, commands, agents)
- Skills are symlinked to all target IDE directories
- MCP configs are merged into `~/.claude.json`, `~/.cursor/mcp.json`, `~/.gemini/antigravity/mcp_config.json`
- Hooks are aggregated and deduplicated (no more 42x duplication)
- Security review gate displays changes before writing
- `nexus.lock.yml` tracks what was deployed where
- `nexus clean` removes all tracked artifacts cleanly
