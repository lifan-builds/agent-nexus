# Agent Nexus Security Model

Agent Nexus writes to global IDE configuration, so the safety model is designed
around review, merge preservation, and traceability.

## Files Nexus Reads

- `nexus.personal.yml` when present, otherwise `nexus.yml`
- `nexus.example.yml` when running `nexus init`
- package contents fetched into `.nexus/cache/`
- previous lockfile: `nexus.personal.lock.yml` or `nexus.lock.yml`
- local package files for dashboard skill token-footprint estimates
- existing target config files before merge:
  - `~/.claude.json`
  - `~/.cursor/mcp.json`
  - `~/.gemini/antigravity/mcp_config.json`
  - `~/.codex/config.toml`
  - `~/.codex/hooks.json` or `$CODEX_HOME/hooks.json`

## Files Nexus Writes

- `nexus.personal.yml` when `nexus init` is run or when the dashboard saves manifest edits
- `.nexus/cache/` package snapshots
- `.nexus/generated/<target>/skills/<skill>/` for metadata overlays
- target skill symlinks:
  - `~/.claude/skills/`
  - `~/.cursor/skills/`
  - `~/.gemini/antigravity/skills/`
  - `~/.codex/skills/`
- target MCP config files listed above
- repo-local hook outputs:
  - `.cursor/hooks.json`
  - `.github/hooks/`
- Codex hook config:
  - `~/.codex/hooks.json` or `$CODEX_HOME/hooks.json`
- lockfile:
  - `nexus.personal.lock.yml` or `nexus.lock.yml`

## Review Gate

`nexus sync` prints a security review before writing MCP config:

```text
==> Security review - MCP servers to be registered:

    context7                       stdio: npx -y @upstash/context7-mcp@latest
```

Without `--yes`, Nexus asks for confirmation before applying those executable
MCP changes. `nexus sync --dry-run` prints the same review and exits without
persistent cache, generated overlays, target config, hooks, or lockfile writes.
Uncached GitHub packages are inspected in temporary storage. Browser MCPs such as
Playwright should be optional when they are not required for every agent session.
Declining a previously managed optional MCP removes it from target configs during
the next accepted sync.

Hooks are executable too. `sync --dry-run` and interactive `sync` print hook commands before writing hook config. Nexus only removes managed Codex hook commands marked with `--nexus-package`; unmanaged user hook commands are preserved.

## Dashboard Safety

`nexus dashboard` starts a local management UI on `127.0.0.1` by default. Passive
page load is read-only: it reads the manifest, lockfile, local package files, and
target configs to build status and estimate token footprint.

Dashboard writes are limited to explicit actions:

- target-policy saves validate the selected target list and atomically replace the
  manifest targets block,
- package skill-policy saves validate the selected package and skills, then update
  only `packages[].skills` and the manual-invocation fields under
  `packages[].skill_overrides`,
- raw manifest saves use redacted text, validation, atomic replacement, and a manifest revision check,
- deploy actions rebuild the reviewed plan and require the same plan hash, manifest revision, and exact confirmation string.

Skill-policy saves are structured writes and do not require MCP env/header values in the browser payload. The advanced manifest editor never returns real secret values to the browser.

The dashboard sanitizes MCP env and header values before returning state to the
browser. It shows env/header key names only. Token and cost values are static
estimates plus optional manifest metadata; they are not live provider billing.

## MCP Merge Rules

For JSON MCP config targets, Nexus:

- creates the required config shape if the file does not exist,
- preserves unmanaged MCP servers not declared in the manifest,
- updates manifest-managed command, args, URL, and transport fields,
- preserves local-only keys on an existing server entry,
- preserves existing env values when the manifest value is a placeholder such
  as `${GITHUB_TOKEN}`,
- keeps local env keys that are not mentioned in the manifest.

For Codex TOML config, Nexus writes only between:

```toml
# BEGIN NEXUS MANAGED MCP SERVERS
# END NEXUS MANAGED MCP SERVERS
```

Content outside that block is left intact. Inside the managed block, existing
env values are kept when the manifest value is a placeholder such as
`${GITHUB_TOKEN}`; this prevents a real local token from being replaced by the
literal placeholder on repeat syncs.

## Hook Dedupe Rules

Cursor hooks are deduplicated by hashing normalized hook entries with Nexus
metadata stripped. Codex hooks are merged with unmanaged entries, stale
Nexus-managed commands are removed, and the final hook entries are deduplicated
by content.

This prevents repeated managed hook entries from accumulating across syncs while
leaving user-owned hook commands alone. Read [hooks.md](hooks.md) for target-specific hook behavior.

## Lockfile Traceability

Every sync writes a lockfile that records:

- Nexus version and generation time,
- resolved package cache path,
- discovered skills, hooks, commands, and agents,
- target deployment list for each package,
- generated metadata overlay paths,
- managed MCP server names.

Package cache directories are content-addressed by commit SHA, so a target
symlink can be traced back to a specific fetched package snapshot.

## Safe Verification Path

Use this sequence on a new machine:

```bash
python nexus.py audit
python nexus.py init
python nexus.py sync --dry-run
python nexus.py sync
python nexus.py doctor
```

Stop after the dry run if an MCP command or hook source is not expected.
