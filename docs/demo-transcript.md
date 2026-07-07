# Release Demo Transcript

This transcript shows the release-readiness path a new developer should be able
to follow. Exact package names and counts depend on the manifest, but the
security review, lockfile, hook dedupe, and doctor steps are stable behavior.

## 1. Audit Existing Config

```bash
$ python nexus.py audit --redact-home
==> nexus audit

Targets:
  + claude: ~/.claude
  + cursor: ~/.cursor
  - antigravity: ~/.gemini/antigravity
  + codex: ~/.codex

MCP servers:
  claude:
    nexus-managed: context7
    unmanaged: github
  cursor:
    nexus-managed: none
    unmanaged: none

Skills:
  claude: 6 Nexus symlinks, 1 unmanaged dirs, 0 stale symlinks
  cursor: 6 Nexus symlinks, 0 unmanaged dirs, 0 stale symlinks

Hooks:
  codex: 3 managed commands, 0 unmanaged commands
```

`nexus audit` is read-only: it detects target roots, MCP servers, skill links,
stale symlinks, hooks, and lockfile state without fetching packages or writing
config.

## 2. Initialize

```bash
$ python nexus.py init
  + Created nexus.personal.yml from nexus.example.yml
Edit nexus.personal.yml for your machine, then run 'nexus sync --dry-run'.
```

`nexus init` creates a personal manifest instead of asking users to edit the
checked-in example.

## 3. Dry Run And Security Review

```bash
$ python nexus.py sync --dry-run
==> Resolving optional MCPs...
==> Fetching packages...
  + context-harness (local or fetched)
==> Security review - MCP servers to be registered:

    sequential-thinking            stdio: npx -y @modelcontextprotocol/server-sequential-thinking
    playwright                     stdio: npx -y @playwright/mcp@latest
    context7                       stdio: npx -y @upstash/context7-mcp@latest

==> Dry run - no target configs or lockfiles written.

==> Would deploy:
  skill: context-harness -> claude,cursor,antigravity,codex
  skill: context-init -> claude,cursor,antigravity,codex
    overlay: claude skill_frontmatter
    overlay: cursor skill_frontmatter
    overlay: antigravity skill_frontmatter
    overlay: codex skill_frontmatter
  skill: context-catch-up -> claude,cursor,antigravity,codex
  skill: set-goal -> claude,cursor,antigravity,codex
  skill: context-maintain -> claude,cursor,antigravity,codex
  skill: context-upgrade -> claude,cursor,antigravity,codex
  hooks: context-harness -> codex (~/.codex/hooks.json)
```

The dry run proves the review surface before writing target IDE config or
lockfiles. When hooks are configured, the dry run also prints the hook commands
that will be installed.

## 4. Sync

```bash
$ python nexus.py sync
==> Resolving optional MCPs...
==> Fetching packages...
==> Security review - MCP servers to be registered:
...
  ? Apply these changes? [y/N] y
==> Pruning stale skills...
==> Deploying skills...
  + context-harness -> claude,cursor,antigravity,codex
  + context-init -> claude,cursor,antigravity,codex
  + context-catch-up -> claude,cursor,antigravity,codex
  + set-goal -> claude,cursor,antigravity,codex
  + context-maintain -> claude,cursor,antigravity,codex
  + context-upgrade -> claude,cursor,antigravity,codex
==> Deploying hooks...
  + Codex hooks: merged 3 entries into ~/.codex/hooks.json
==> Syncing MCP servers...
  + sequential-thinking (added)
  + playwright (added)
  + context7 (added)
==> Generating lockfile...
  + nexus.personal.lock.yml written

==> Sync complete!
  6 skills processed; deployed counts: claude=6, cursor=6, antigravity=6, codex=6
  MCP servers synced to: ~/.claude/.mcp.json, ~/.cursor/mcp.json, ~/.gemini/antigravity/mcp_config.json, ~/.codex/config.toml
```

## 5. MCP Merge Behavior

Before sync:

```json
{
  "mcpServers": {
    "user-only": {"command": "custom"},
    "github": {
      "command": "/old/npx",
      "args": ["old"],
      "env": {
        "GITHUB_TOKEN": "real-token",
        "LOCAL_ONLY": "keep"
      },
      "localSetting": true
    }
  }
}
```

Manifest:

```yaml
mcps:
  - name: github
    command: npx
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_TOKEN: "${GITHUB_TOKEN}"
```

After sync, `user-only`, `LOCAL_ONLY`, `localSetting`, and the real token remain,
while the managed command and args are updated.

## 6. Lockfile Output

```yaml
packages:
  - name: context-harness
    path: .nexus/cache/github.com/lifan-builds/context-harness/<commit>
    discovered:
      skills:
        - context-harness
        - context-init
        - context-catch-up
        - set-goal
        - context-maintain
        - context-upgrade
      hooks_codex: true
      commands: []
      agents: []
    deployed_to:
      - claude
      - cursor
      - antigravity
      - codex
    overlays:
      - skill: context-init
        target: claude
        type: skill_frontmatter
        path: .nexus/generated/claude/skills/context-init
      - skill: context-init
        target: cursor
        type: skill_frontmatter
        path: .nexus/generated/cursor/skills/context-init
      - skill: context-init
        target: antigravity
        type: skill_frontmatter
        path: .nexus/generated/antigravity/skills/context-init
      - skill: context-init
        target: codex
        type: skill_frontmatter
        path: .nexus/generated/codex/skills/context-init
mcps:
  managed:
    - name: sequential-thinking
    - name: playwright
    - name: context7
```

The path points to the immutable package snapshot used by deployed symlinks.

## 7. Doctor

```bash
$ python nexus.py doctor
==> nexus doctor - v0.2.0
  + nexus.personal.yml found
  + nexus.personal.yml is valid YAML
  + Package cache: 1 packages cached
  + nexus.personal.lock.yml exists
  + claude skills: 6 symlinks
  + cursor skills: 6 symlinks
  + antigravity skills: 6 symlinks
  + codex skills: 6 symlinks
  + claude MCP config: 3 servers (~/.claude/.mcp.json)
  + cursor MCP config: 3 servers (~/.cursor/mcp.json)
  + antigravity MCP config: 3 servers (~/.gemini/antigravity/mcp_config.json)
  + codex MCP config: 3 servers (~/.codex/config.toml)
  + Codex hooks: 3 entries (~/.codex/hooks.json)
```

## 8. Dashboard

```bash
$ python nexus.py dashboard --json
{
  "meta": {
    "nexus_version": "0.2.0",
    "manifest_path": ".../nexus.personal.yml",
    "lockfile_path": ".../nexus.personal.lock.yml",
    "lockfile_exists": true
  },
  "summary": {
    "targets": 4,
    "packages": 1,
    "skills": 6,
    "managed_mcps": 3
  }
}
```

For interactive management:

```bash
$ python nexus.py dashboard --no-open
==> Agent Nexus dashboard running at http://127.0.0.1:8765/
  Press Ctrl-C to stop.
```

The dashboard shows inventory, global target policy, platform status, and per-skill/per-MCP token footprint in one place. It can update the global target list and trigger `nexus sync` only after an explicit confirmation.

## 9. Context Harness Proof

Context Harness is a normal Nexus package. When present in the manifest, it is
fetched, discovered by `SKILL.md`, deployed as skill symlinks, and its Codex hook
file is merged through the same managed hook path as any other package.
