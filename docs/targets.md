# Target And Resource Matrix

Agent Nexus deploys a single manifest into native target files for Claude Code, Cursor, Google Antigravity, and Codex. This page separates implemented deployment behavior from discovery-only and planned behavior.

## Summary

| Resource | Claude Code | Cursor | Antigravity | Codex | Status |
| --- | --- | --- | --- | --- | --- |
| Skills | symlinked into `~/.claude/skills/` | symlinked into `~/.cursor/skills/` | symlinked into `~/.gemini/antigravity/skills/` | symlinked into `~/.codex/skills/` | implemented |
| MCP stdio | merged into `~/.claude/.mcp.json` | merged into `~/.cursor/mcp.json` | merged into `~/.gemini/antigravity/mcp_config.json` | written inside a managed block in `~/.codex/config.toml` | implemented |
| MCP SSE URL | merged as `type: sse` + `url` | merged as `type: sse` + `url` | merged as `serverUrl` | written as `type = "sse"` + `url` | implemented |
| MCP HTTP URL | merged as `type: http` + `url` | merged as `type: http` + `url` | merged as `serverUrl` | written as `url` | implemented |
| MCP env placeholders | preserves existing local env values when manifest uses `${TOKEN}` | preserves existing local env values when manifest uses `${TOKEN}` | preserves existing local env values when manifest uses `${TOKEN}` | preserves existing local env values inside the managed block | implemented |
| Hooks | copies package hook files into repo `.github/hooks/` | merges package hooks into repo `.cursor/hooks.json` | not deployed | merges managed commands into `~/.codex/hooks.json` or `$CODEX_HOME/hooks.json` | partial |
| Commands | discovered from `commands/*.md` | discovered from `commands/*.md` | discovered from `commands/*.md` | discovered from `commands/*.md` | lockfile only |
| Agents | discovered from `agents/*.md` | discovered from `agents/*.md` | discovered from `agents/*.md` | discovered from `agents/*.md` | lockfile only |
| Target overlays | materialized under `.nexus/generated/claude/skills/` | materialized under `.nexus/generated/cursor/skills/` | materialized under `.nexus/generated/antigravity/skills/` | materialized under `.nexus/generated/codex/skills/` | implemented |
| Lockfile | records package discovery, target deploys, overlays, and managed MCP names | records package discovery, target deploys, overlays, and managed MCP names | records package discovery, target deploys, overlays, and managed MCP names | records package discovery, target deploys, overlays, and managed MCP names | implemented |
| Doctor | checks skill links, MCP config, overlays, and hook status where applicable | checks skill links, MCP config, overlays, and hook status where applicable | checks skill links, MCP config, and overlays | checks skill links, MCP config, overlays, and hooks | implemented |
| Audit | read-only inventory | read-only inventory | read-only inventory | read-only inventory | implemented |

## Target Details

### Claude Code

- Skills are managed symlinks in `~/.claude/skills/`.
- MCP servers are merged into `~/.claude/.mcp.json` using the `mcpServers` shape.
- Package hook files for Claude are copied into repo-local `.github/hooks/`.
- Commands and agents are discovered and recorded in the lockfile, but Nexus does not deploy native command or agent files yet.

### Cursor

- Skills are managed symlinks in `~/.cursor/skills/`.
- MCP servers are merged into `~/.cursor/mcp.json` using the `mcpServers` shape.
- Package hook files for Cursor are merged into repo-local `.cursor/hooks.json` and deduplicated by normalized content.
- Commands and agents are discovered and recorded in the lockfile, but Nexus does not deploy native command or agent files yet.

### Google Antigravity

- Skills are managed symlinks in `~/.gemini/antigravity/skills/`.
- MCP servers are merged into `~/.gemini/antigravity/mcp_config.json` using the `mcpServers` shape.
- URL-based MCPs are written with `serverUrl` for Antigravity.
- Hooks are not deployed for Antigravity yet.
- Commands and agents are discovered and recorded in the lockfile, but Nexus does not deploy native command or agent files yet.

### Codex

- Skills are managed symlinks in `~/.codex/skills/`.
- MCP servers are written into the Nexus-managed block in `~/.codex/config.toml`.
- Content outside the managed MCP block is preserved.
- Codex hooks are merged into `~/.codex/hooks.json`, or `$CODEX_HOME/hooks.json` when `CODEX_HOME` is set.
- Stale managed Codex hook commands are removed only when marked with `--nexus-package`.
- Commands and agents are discovered and recorded in the lockfile, but Nexus does not deploy native command or agent files yet.

## Status Definitions

- **Implemented** means Nexus writes or verifies the target resource today and tests cover the core behavior.
- **Partial** means Nexus supports some target/resource behavior, but the behavior is intentionally narrower than a complete native integration.
- **Lockfile only** means Nexus discovers the asset and records it for traceability, but does not deploy a native target file.
- **Planned** means the roadmap calls for the capability, but the current CLI does not implement it.
