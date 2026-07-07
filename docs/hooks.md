# Hook Lifecycle

Hooks are executable configuration, so Agent Nexus treats them as reviewable managed assets rather than invisible package contents.

## Discovery Paths

Nexus discovers hook files from each package using target-specific file names:

| Target | Package hook paths | Deployment behavior |
| --- | --- | --- |
| Claude Code | `hooks/hooks.json` or `hooks.json` | copied into repo-local `.github/hooks/` |
| Cursor | `hooks/hooks-cursor.json` or `hooks-cursor.json` | merged into repo-local `.cursor/hooks.json` |
| Google Antigravity | none | not deployed |
| Codex | `hooks/hooks-codex.json` or `hooks-codex.json` | merged into `~/.codex/hooks.json` or `$CODEX_HOME/hooks.json` |

Use a package `hooks` filter to restrict hook deployment:

```yaml
packages:
  - repo: lifan-builds/context-harness
    ref: main
    hooks:
      - codex
```

Use `hooks: false` or `hooks: []` to disable hook deployment from a package.

## Review Output

`nexus sync --dry-run` and interactive `nexus sync` print hook commands before writing hook config:

```text
==> Hook review - executable hook commands to be installed:

    context-harness                codex    node "/path/to/package/hook.js" --nexus-package context-harness
```

For hooks that do not contain a direct command field, Nexus prints the hook file path so the user can inspect it before approving sync.

## Executable Timing

Nexus does not execute hook commands during discovery, dry run, or sync. It installs hook configuration for the target tool. The target tool decides when to run the hook based on that target's hook events.

Review hook commands and referenced scripts before syncing packages you do not already trust.

## Cursor Hooks

Cursor hook files are merged into `.cursor/hooks.json`. Nexus deduplicates entries by hashing normalized hook entries with Nexus metadata keys removed. This prevents repeated package syncs from accumulating duplicate managed hook entries.

Cursor hook output is generated from package hook files; Nexus does not merge an existing repo-local `.cursor/hooks.json` as unmanaged input today.

## Codex Hooks

Codex hooks are merged with existing `~/.codex/hooks.json`, or `$CODEX_HOME/hooks.json` when `CODEX_HOME` is set.

Nexus-managed Codex hook commands are identified by the marker `--nexus-package`. During sync, Nexus removes stale commands with that marker before adding currently selected package hooks. Commands without that marker are treated as unmanaged user hooks and preserved.

Nexus also replaces `{{package_root}}` placeholders in package hook commands with the resolved package path before writing the hook config.

## Claude And Antigravity Hooks

Claude hook files are copied into repo-local `.github/hooks/`. This makes copied package hook files inspectable in the repository workspace.

Antigravity hook deployment is not supported yet. The target matrix lists Antigravity hooks as not deployed.

## Safety Guarantees

- Dry-run shows hook targets and hook commands without writing hook config.
- Managed Codex hooks are pruned only when marked with `--nexus-package`.
- Unmanaged Codex hook commands are preserved.
- Cursor hook entries are deduplicated by normalized content.
- Antigravity hooks are not silently installed.
