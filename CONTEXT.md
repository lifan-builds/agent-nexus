# Context
<!-- context-harness:schema v2 -->

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

### Objectives
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
