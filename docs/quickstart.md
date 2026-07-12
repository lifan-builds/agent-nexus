# Quickstart

## Install

Until a PyPI release is published, install directly from GitHub:

```bash
uv tool install 'agent-nexus @ git+https://github.com/lifan-builds/agent-nexus.git'
# or
pipx install 'git+https://github.com/lifan-builds/agent-nexus.git'
```

Contributors can clone the repository and run `scripts/install-local.sh`.

## Safe first run

From the workspace you want to manage:

```bash
nexus audit --redact-home
nexus init
$EDITOR nexus.personal.yml
nexus sync --dry-run --no-optional
nexus sync
nexus doctor
```

`nexus init` creates an empty starter: no packages, MCPs, or hooks are enabled. Use `nexus init --template example` only when you explicitly want the comprehensive example.

A dry-run may read the network, but uncached package discovery uses temporary storage and leaves no persistent Nexus cache or target changes.

## Optional MCPs

```bash
nexus sync --dry-run --include-optional playwright
nexus sync --include-optional playwright
```

Use `--all` to include every optional MCP or `--no-optional` to skip all prompts.

## Dashboard

```bash
nexus dashboard
```

The dashboard can initialize an empty workspace, edit a redacted manifest, preview a plan, and deploy only while that reviewed plan remains current.

## Workspace selection

Nexus uses `--project-dir`, then `NEXUS_PROJECT_DIR`, then the nearest parent with a Nexus manifest. Pre-init commands use the current directory.
