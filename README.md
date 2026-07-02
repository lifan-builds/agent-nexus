# Agent Nexus

Agent Nexus is a Python CLI for managing AI agent environments from one
versioned manifest. It fetches packages, discovers their assets, deploys skills
and hooks to supported IDEs, merges MCP server configuration, and writes a
lockfile that shows what was installed where.

Nexus is not a replacement for native Codex, Claude, Cursor, or Kasetto
workflows. It is a small cross-IDE deployment layer for developers who want one
repo-local source of truth for repeatable agent setup.

## Quick Start

Prerequisites:

- Python 3.10+
- PyYAML: `python -m pip install pyyaml`
- Git
- Node.js only for MCP servers that run through `npx`

```bash
git clone https://github.com/lifan-builds/agent-nexus.git ~/Project/agent-nexus
cd ~/Project/agent-nexus
python nexus.py init
python nexus.py sync --dry-run
python nexus.py sync
python nexus.py doctor
```

Expected first dry run:

```text
==> Security review - MCP servers to be registered:

    sequential-thinking            stdio: npx -y @modelcontextprotocol/server-sequential-thinking
    playwright                     stdio: npx -y @playwright/mcp@latest
    context7                       stdio: npx -y @upstash/context7-mcp@latest

==> Dry run - no target configs or lockfiles written.
==> Would deploy:
  skill: context-harness -> claude,cursor,antigravity,codex
  skill: context-init -> claude,cursor,antigravity,codex
  skill: context-catch-up -> claude,cursor,antigravity,codex
  skill: set-goal -> claude,cursor,antigravity,codex
  skill: context-maintain -> claude,cursor,antigravity,codex
  skill: context-upgrade -> claude,cursor,antigravity,codex
  hooks: context-harness -> codex (~/.codex/hooks.json)
```

`nexus init` creates `nexus.personal.yml` from `nexus.example.yml`. Edit that
personal manifest for your machine before the first real sync.

## What Nexus Does

- Uses one YAML manifest for packages, MCP servers, optional MCPs, and targets.
- Fetches GitHub packages into immutable `.nexus/cache/` snapshots keyed by
  commit SHA.
- Auto-discovers package assets from files instead of requiring package type
  classification.
- Deploys skills by symlink to the configured IDE targets.
- Merges MCP server configs while preserving unmanaged servers and local env
  secrets.
- Aggregates hooks and deduplicates them by normalized content.
- Writes `nexus.lock.yml` or `nexus.personal.lock.yml` with discovered assets,
  target deployment, and generated overlay paths.
- Supports target-specific skill metadata overlays, including Codex
  `agents/openai.yaml` policy/interface metadata.

## Target And Asset Matrix

| Surface | Nexus behavior | Claude Code | Cursor | Google Antigravity | Codex |
| --- | --- | --- | --- | --- | --- |
| Skills | Discovered by `SKILL.md`; deployed as managed symlinks | `~/.claude/skills/` | `~/.cursor/skills/` | `~/.gemini/antigravity/skills/` | `~/.codex/skills/` |
| Hooks | Discovered from target hook files; deduplicated before write | copied to repo `.github/hooks/` | merged to repo `.cursor/hooks.json` | not deployed | merged to `~/.codex/hooks.json` or `$CODEX_HOME/hooks.json` |
| MCP servers | Declared inline in manifest; review shown before write | global `~/.claude/.mcp.json` | `~/.cursor/mcp.json` | `~/.gemini/antigravity/mcp_config.json` | managed TOML block in `~/.codex/config.toml` |
| Commands | Discovered from `commands/*.md` and recorded in lockfile | deployment pending | deployment pending | deployment pending | deployment pending |
| Agents | Discovered from `agents/*.md` and recorded in lockfile | deployment pending | deployment pending | deployment pending | deployment pending |
| Plugins | Not managed as native plugin bundles | use native plugin system | use native extensions/rules | use native config | use native Codex plugins |
| Config merge | Preserves unmanaged config and local-only keys | yes | yes | yes | preserves content outside Nexus managed block |
| Lockfile | Records resolved package path, discovered assets, deployment targets, and overlays | yes | yes | yes | yes |

## Security Model

Read [docs/security-model.md](docs/security-model.md) before running a real
`sync` against a personal machine. In short:

- `sync --dry-run` may populate `.nexus/cache/`, prints MCP review output, and
  exits before writing target IDE config or lockfiles.
- A real `sync` prompts before registering executable MCP commands unless
  `--yes` is passed.
- Existing MCP servers not declared in the manifest stay in place.
- Existing env values are kept when the manifest uses `${VAR}` placeholders, so
  a local token is not replaced by a literal placeholder.
- Codex MCP config is isolated in a `BEGIN NEXUS MANAGED MCP SERVERS` block.
- Hooks marked with `--nexus-package` are treated as Nexus-managed; unmanaged
  user hooks are preserved.

## Ecosystem Positioning

Current public docs for Kasetto, Codex, Claude Code, and Cursor all describe
native or declarative ways to manage agent capabilities. Nexus should be chosen
for its repo-local implementation details, not because another tool is assumed
to lack a feature.

Use Nexus when you want:

- One manifest checked in with this repository.
- Package auto-discovery across skills, hooks, commands, and agents.
- Hook lifecycle cleanup and deduplication across managed packages.
- MCP security review before executable config is written.
- Target-specific deployment and metadata overlays.
- Lockfile traceability for every sync.
- Context Harness deployment as a normal package.

Use native plugin systems when you want marketplace distribution, IDE-specific
UI, or first-party install/update flows. Use Kasetto when you want its Rust
binary, broader agent preset catalog, and ecosystem conventions.

## Demo Proof

See [docs/demo-transcript.md](docs/demo-transcript.md) for a release-readiness
transcript covering:

- `nexus init`
- `sync --dry-run` security review
- real `sync` lifecycle
- hook deduplication
- MCP merge behavior
- lockfile output
- `doctor`
- Context Harness deployment

## Manifest Basics

```yaml
name: agent-nexus
version: 1.0.0

targets:
  - claude
  - cursor
  - antigravity
  - codex

packages:
  - repo: lifan-builds/context-harness
    ref: main
    hooks:
      - codex

mcps:
  - name: sequential-thinking
    command: npx
    args: ["-y", "@modelcontextprotocol/server-sequential-thinking"]
```

Package entries can also use `targets`, `skills`, `sparse_paths`, and
`skill_overrides`. See [nexus.example.yml](nexus.example.yml) for the full
template.

## Troubleshooting

`Error: PyYAML is required`

Run:

```bash
python -m pip install pyyaml
```

`Error: git is required`

Install Git and make sure it is on `PATH`.

`npx` MCP servers fail after sync

Install Node.js or change the MCP entry to a command available on your machine.

`nexus doctor` reports missing MCP config

Run `python nexus.py sync --dry-run` first, review the MCP commands, then run
`python nexus.py sync` if the review is acceptable.

`nexus.personal.yml already exists`

`nexus init` refuses to overwrite personal config. Use `python nexus.py init
--force` only when you want to replace it with the example template.

## Development

Run focused verification:

```bash
python -m pytest tests
python -m py_compile nexus.py
python nexus.py sync --dry-run
python nexus.py doctor
```

The Python CLI intentionally has one runtime dependency: PyYAML.
