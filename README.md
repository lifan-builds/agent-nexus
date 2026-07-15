# Agent Nexus

<p align="center">
  <img src="docs/assets/nexus-icon.svg" alt="Agent Nexus icon" width="96" height="96">
</p>

<p align="center">
  <strong>The safe package manager for your agent workspace.</strong><br />
  Declare MCPs, skills, hooks, and agent packages once. Preview every executable change, sync native config, verify with doctor, and trace the result with a lockfile.
</p>

<p align="center">
  <img alt="Python 3.10+" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white">
  <img alt="License" src="https://img.shields.io/badge/License-MIT-31d0aa?style=flat-square">
  <img alt="Local first" src="https://img.shields.io/badge/local--first-dashboard-0d1824?style=flat-square">
  <img alt="Review first" src="https://img.shields.io/badge/review--first-sync-0d1824?style=flat-square">
  <img alt="Lockfile traceability" src="https://img.shields.io/badge/lockfile-traceability-0d1824?style=flat-square">
</p>

<p align="center">
  <a href="#5-minute-safe-start"><img alt="Quickstart" src="https://img.shields.io/badge/Quickstart-Install%20safely-31d0aa?style=for-the-badge"></a>
  <a href="#dashboard"><img alt="Dashboard" src="https://img.shields.io/badge/Dashboard-Review%20workspace-65a7ff?style=for-the-badge"></a>
  <a href="docs/security-model.md"><img alt="Security model" src="https://img.shields.io/badge/Security-Review%20model-0d1824?style=for-the-badge"></a>
  <a href="docs/comparison.md"><img alt="Comparison guide" src="https://img.shields.io/badge/Compare-Category%20guide-0d1824?style=for-the-badge"></a>
</p>

<p align="center">
  <img src="docs/assets/dashboard-hero.png" alt="Agent Nexus dashboard showing package inventory, target policy, platform status, and token estimates" width="920">
</p>

<p align="center">
  <code>nexus.personal.yml</code> → dry-run review → sync native config → doctor → lockfile
</p>

---

## Why Nexus?

Agent workspaces sprawl fast: Claude Code, Cursor, Google Antigravity, and Codex each have their own places for skills, MCP servers, hooks, and config. Useful capabilities also live in GitHub repos, local folders, docs, and one-off install notes.

Agent Nexus turns that into one reviewable workflow:

| Before | After |
| --- | --- |
| Hand-edit four target configs | Declare the stack once in `nexus.personal.yml` or `nexus.yml` |
| Copy MCP commands into different formats | Preview executable MCP and hook changes before writing |
| Wonder which package installed what | Trace deployed assets back to package snapshots and a lockfile |
| Check each tool manually | Run `doctor` and inspect the localhost dashboard |

<p align="center">
  <img src="docs/assets/trust-path.svg" alt="Agent Nexus flow from manifest to dry-run review, sync, doctor verification, and lockfile traceability" width="920">
</p>

## The 30-second demo

```yaml
name: my-agent-workspace
version: 1.0.0

targets:
  - claude
  - cursor
  - antigravity
  - codex
# Use targets: ["*"] only when you want all 41 skill target presets.

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

```bash
nexus audit --redact-home
nexus sync --dry-run
nexus sync
nexus doctor
```

`audit` reads local state without writing. `sync --dry-run` shows the MCP and hook review before target config changes. `sync` applies the reviewed plan. `doctor` verifies what landed.

## 5-minute safe start

### 1. Install

You need Python 3.10+ and Git. Node.js is needed only for MCP servers that use `npx`.

Until a PyPI release is published, install directly from GitHub:

```bash
uv tool install 'agent-nexus @ git+https://github.com/lifan-builds/agent-nexus.git'
# or
pipx install 'git+https://github.com/lifan-builds/agent-nexus.git'
```

For contributor/source-checkout mode:

```bash
git clone https://github.com/lifan-builds/agent-nexus.git ~/.agent-nexus
cd ~/.agent-nexus
scripts/install-local.sh
```

The source installer creates a reversible `~/.local/bin/nexus` symlink. See the [quickstart](docs/quickstart.md) for virtual-environment install and uninstall options.

### 2. Choose the workspace

Run Nexus from the workspace you want to manage. It uses `--project-dir`, then `NEXUS_PROJECT_DIR`, then the nearest parent containing a Nexus manifest.

### 3. Inspect, initialize, preview

```bash
nexus audit --json --redact-home
nexus init
nexus sync --dry-run
```

`nexus init` creates a safe empty `nexus.personal.yml` with no packages, MCPs, or hooks. Use `nexus init --template example` only when you explicitly want the comprehensive example. Commit `nexus.yml` only for a reviewed shared team stack.

### 4. Deploy after review

```bash
nexus sync
nexus doctor
```

Dry-run uses temporary storage for uncached packages and leaves no persistent target or Nexus-cache changes. A real sync prints the review and asks for approval unless you pass `--yes`.

## Let your agent install it

Paste this into Claude Code, Codex, Cursor, or another coding agent from the directory where you want Agent Nexus installed:

```text
Install Agent Nexus for me safely.

Goal:
- Set up Agent Nexus as the review-first package manager for my coding-agent workspace.
- Use a personal manifest unless I explicitly ask for a committed team manifest.
- Do not overwrite existing agent config without showing me the dry-run output first.

Steps:
1. Check that Python 3.10+, Git, and PyYAML are available. If PyYAML is missing, install it with `python -m pip install pyyaml` after asking me if needed.
2. Clone `https://github.com/lifan-builds/agent-nexus.git` to `~/.agent-nexus`, or use the existing checkout if I am already inside one.
3. Run `scripts/install-local.sh` to install the reversible `~/.local/bin/nexus` wrapper, or keep using `python nexus.py` if `~/.local/bin` is not on PATH.
4. Run `nexus audit --redact-home` and summarize detected targets and existing managed assets.
5. Run `nexus init` only if `nexus.personal.yml` does not already exist.
6. Help me edit `nexus.personal.yml` with targets, packages, skill filters, MCP servers, and `${ENV_VAR}` placeholders for secrets.
7. Run `nexus sync --dry-run` and show me the MCP commands, hook commands, and deployment plan.
8. Stop and ask for my approval before running a real sync.
9. After I approve, run `nexus sync`, then `nexus doctor`.
10. Report the lockfile path, warnings, and the next command I should run if something failed.

Safety rules:
- Prefer `nexus.personal.yml` for local setup.
- Keep secrets out of git; use `${ENV_VAR}` placeholders.
- Do not pass `--yes` unless I explicitly ask for unattended setup.
- Do not delete or overwrite unmanaged Claude Code, Cursor, Antigravity, or Codex config.
```

For unattended setup after you already trust the manifest:

```bash
nexus sync --yes
```

## Dashboard

```bash
nexus dashboard
```

The dashboard is a localhost-only review console for the same workflow as the CLI:

- Start with deploy readiness and the next safe step: preview the dry-run review.
- Inspect package source, discovered assets, skill policy, MCP servers, target health, and lockfile state.
- Tune package skill policy and global target policy in the manifest.
- Run deploy only after the dashboard asks you to type `deploy`.

<p align="center">
  <img src="docs/assets/dashboard-management.png" alt="Agent Nexus dashboard target policy and platform health view with confirmed deploy controls" width="920">
</p>

For scripting or troubleshooting without starting the server:

```bash
nexus dashboard --json
```

Use `--no-open` when you want the server URL without automatically opening a browser.

## What Nexus manages

| Capability | What Nexus does |
| --- | --- |
| One manifest | Keep agent capabilities in `nexus.yml` or a gitignored `nexus.personal.yml`. |
| GitHub/local packages | Fetch package snapshots, discover skills, hooks, commands, and agents, and record them in the lockfile. |
| MCP servers | Merge declared MCP servers into tested target config formats while preserving unmanaged entries and local secrets. |
| Skills | Link package skills into selected targets and support package-level skill filters. |
| Hooks | Review managed hook commands, deploy supported target hooks, and deduplicate stale managed entries. |
| Target overlays | Generate target-specific skill metadata without mutating package snapshots. |
| Dashboard controls | Inspect state, tune skill and target policy, and run a confirmed deploy from localhost. |
| Traceability | Record resolved packages, deployed resources, overlays, and managed MCPs in `nexus.lock.yml`. |

## Browser tooling policy

Keep browser access narrow and intentional, using this routing order:

1. Use built-in **WebSearch/WebFetch** for ordinary research and static page retrieval.
2. Use **Kimi WebBridge** when the user's real browser, existing login sessions, interactive controls, dynamic pages, or screenshots are required.
3. Use **Chrome DevTools MCP** only for focused Lighthouse, performance-trace, Core Web Vitals, or heap diagnostics, or when the user explicitly requests it. Keep it target-local rather than Nexus-managed by default.

**Playwright MCP** remains optional for isolated, reproducible browser automation and end-to-end testing. Put it under `optional_mcps` rather than enabling it for every sync.

See [docs/mcp.md](docs/mcp.md) for configuration and pruning behavior.

## Supported targets

Nexus focuses on **four tested native targets** and can deploy skills to **41 target presets** when you opt in.

| Target | Skills | MCP servers | Hooks |
| --- | --- | --- | --- |
| Claude Code | `~/.claude/skills/` | `~/.claude.json` | repo `.github/hooks/` |
| Cursor | `~/.cursor/skills/` | `~/.cursor/mcp.json` | repo `.cursor/hooks.json` |
| Google Antigravity | `~/.gemini/antigravity/skills/` | `~/.gemini/antigravity/mcp_config.json` | not deployed |
| Codex | `~/.codex/skills/` | managed block in `~/.codex/config.toml` | `~/.codex/hooks.json` or `$CODEX_HOME/hooks.json` |

If `targets` is omitted, Nexus uses the four core targets. Use `targets: ["*"]` only when you want skill deployment across all target presets. Additional skill presets are listed in [docs/targets.md](docs/targets.md), along with implemented, partial, lockfile-only, and planned behavior.

## Safety model

Agent Nexus writes to local agent config, so the default path is review-first.

- `audit` inventories local state without writing.
- `sync --dry-run` previews package discovery, MCP commands, hook commands, and deployment plans.
- `sync` prints executable MCP and hook changes before applying them.
- Existing unmanaged MCP servers and local env values are preserved.
- Codex MCP config is isolated inside a Nexus-managed TOML block.
- The dashboard binds to localhost, redacts secrets, and requires typed confirmation before deploy.
- Every sync writes a lockfile for traceability.

Read the full model in [docs/security-model.md](docs/security-model.md). For exact target support, read [docs/targets.md](docs/targets.md). For MCP merge details, read [docs/mcp.md](docs/mcp.md).

## Common workflows

### Keep a personal agent stack synced

```bash
nexus audit --redact-home
nexus init
$EDITOR nexus.personal.yml
nexus sync --dry-run
nexus sync
nexus doctor
nexus dashboard
```

### Share a team-standard agent setup

1. Commit `nexus.yml` to the repo.
2. Put shared packages, skills, MCP names, and targets in that file.
3. Keep secrets out of git with `${ENV_VAR}` placeholders.
4. Ask each developer to run `nexus sync --dry-run` before first deploy.

### Deploy Context Harness everywhere

```yaml
targets: [claude, cursor, antigravity, codex]

packages:
  - repo: lifan-builds/context-harness
    ref: main
    hooks:
      - codex
```

Then:

```bash
nexus sync
```

Context Harness is treated like any other Nexus package: fetched, discovered, deployed, locked, and verified.

## Further reading

- [Manifest reference](docs/manifest.md)
- [Target and resource matrix](docs/targets.md)
- [Package reference](docs/packages.md)
- [Package trust and lockfile traceability](docs/package-trust.md)
- [MCP configuration](docs/mcp.md)
- [Hook lifecycle](docs/hooks.md)
- [Security model](docs/security-model.md)
- [Demo transcript](docs/demo-transcript.md)
- [Screenshot checklist](docs/screenshot-checklist.md)
- [Comparison guide](docs/comparison.md)
- [Example manifests](examples/README.md)
- [Quickstart](docs/quickstart.md)
- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)
- [Changelog](CHANGELOG.md)

## Repository map

- `nexus.py` — supported CLI and localhost dashboard runtime.
- `tests/` — unit, CLI, repository, package, and browser verification.
- `docs/` — user, security, target, package, demo, and release documentation.
- `examples/` — reviewed manifest patterns; not automatic defaults.
- `.github/` — CI and community metadata; only `.github/hooks/` is generated by sync.
- `AGENTS.md` and `.trellis/` — project-local agent activation, workflow, specifications, and task context.
- `nexus.sh` — deprecated historical reference; use `nexus` or `nexus.py`.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `Error: PyYAML is required` | Run `python -m pip install pyyaml`. |
| `Error: git is required` | Install Git and make sure it is available on `PATH`. |
| `npx` MCP servers fail after sync | Install Node.js or change the MCP entry to a command available on your machine. |
| `nexus doctor` reports missing MCP config | Run `nexus sync --dry-run`, then `nexus sync`, then `nexus doctor`. |
| `nexus.personal.yml already exists` | `nexus init` refuses to overwrite personal config. Use `nexus init --force` only when you intentionally want to replace it. |

## Development verification

```bash
python -m pytest tests
python -m py_compile nexus.py
python nexus.py audit --json
python nexus.py sync --dry-run
python nexus.py doctor
python nexus.py dashboard --json
```

Agent Nexus intentionally keeps the runtime small: Python plus PyYAML.

## Positioning

Agent Nexus is not trying to be the broadest possible agent hub, a generic dotfiles sync tool, or a replacement for native plugin systems in Claude Code, Cursor, Antigravity, or Codex.

It is the package-oriented deployment layer for serious agent workspaces:

> Install agent capabilities from GitHub, review every executable change before it touches local config, deploy native target files, and trace the result with a lockfile and doctor.

Use native marketplaces when you want platform-specific discovery and first-party install UX. Use broad hubs when your top priority is maximum target count. Use Agent Nexus when you want a safe, inspectable workflow for keeping MCP servers, skills, hooks, and agent packages consistent across the coding agents you actually use.
