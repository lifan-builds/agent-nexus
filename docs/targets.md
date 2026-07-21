# Target And Resource Matrix

Agent Nexus has **4 core native targets** and **41 skills target presets**. If `targets` is omitted, Nexus selects the core native targets: Claude Code, Cursor, Google Antigravity, and Codex. Use `targets: ["*"]` to deploy skills to every skills preset.

Broad presets are skills-first. MCP and hooks stay disabled unless Nexus has a tested native writer for that target. An individual MCP declaration may use `targets` to select a subset of the configured targets; omitted MCP targets inherit the top-level target set.

## Core Native Targets

| Resource | Claude Code | Cursor | Antigravity | Codex | Status |
| --- | --- | --- | --- | --- | --- |
| Skills | symlinked into `~/.claude/skills/` | symlinked into `~/.cursor/skills/` | symlinked into `~/.gemini/antigravity/skills/` | symlinked into `~/.codex/skills/` | implemented |
| MCP stdio | merged into `~/.claude.json` | merged into `~/.cursor/mcp.json` | merged into `~/.gemini/antigravity/mcp_config.json` | written inside a managed block in `~/.codex/config.toml` | implemented |
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

## Skills Target Presets

| Target key | Display name | Skills path | MCP | Hooks |
| --- | --- | --- | --- | --- |
| `adal` | AdaL | `.adal/skills/` | unsupported | unsupported |
| `amp` | Amp | `~/.config/agents/skills/` | unsupported | unsupported |
| `antigravity` | Google Antigravity | `~/.gemini/antigravity/skills/` | implemented | unsupported |
| `augment` | Augment | `~/.augment/skills/` | unsupported | unsupported |
| `claude` | Claude Code | `~/.claude/skills/` | implemented | implemented |
| `cline` | Cline | `~/.agents/skills/` | unsupported | unsupported |
| `codebuddy` | CodeBuddy | `.codebuddy/skills/` | unsupported | unsupported |
| `codex` | Codex | `~/.codex/skills/` | implemented | implemented |
| `command-code` | Command Code | `.commandcode/skills/` | unsupported | unsupported |
| `continue` | Continue | `~/.continue/skills/` | unsupported | unsupported |
| `crush` | Crush | `.crush/skills/` | planned | unsupported |
| `cursor` | Cursor | `~/.cursor/skills/` | implemented | implemented |
| `droid` | Droid | `.factory/skills/` | unsupported | unsupported |
| `gemini-cli` | Gemini CLI | `~/.gemini/skills/` | unsupported | unsupported |
| `github-copilot` | GitHub Copilot | `~/.copilot/skills/` | unsupported | unsupported |
| `goose` | Goose | `~/.config/goose/skills/` | planned | unsupported |
| `hermes` | Hermes Agent | `~/.hermes/skills/` | planned | unsupported |
| `iflow-cli` | iFlow CLI | `.iflow/skills/` | unsupported | unsupported |
| `junie` | Junie | `~/.junie/skills/` | planned | unsupported |
| `kilo-code` | Kilo Code | `.kilocode/skills/` | unsupported | unsupported |
| `kimi-code` | Kimi Code CLI | `.agents/skills/` | unsupported | unsupported |
| `kiro-cli` | Kiro CLI | `~/.kiro/skills/` | unsupported | unsupported |
| `kode` | Kode | `.kode/skills/` | unsupported | unsupported |
| `mcpjam` | MCPJam | `.mcpjam/skills/` | unsupported | unsupported |
| `mistral-vibe` | Mistral Vibe | `.vibe/skills/` | unsupported | unsupported |
| `mux` | Mux | `.mux/skills/` | unsupported | unsupported |
| `neovate` | Neovate | `.neovate/skills/` | unsupported | unsupported |
| `openclaw` | OpenClaw | `~/.openclaw/skills/` | unsupported | unsupported |
| `opencode` | OpenCode | `~/.config/opencode/skills/` | planned | unsupported |
| `openhands` | OpenHands | `~/.openhands/skills/` | unsupported | unsupported |
| `pi` | Pi | `.pi/skills/` | unsupported | unsupported |
| `pochi` | Pochi | `.pochi/skills/` | unsupported | unsupported |
| `qoder` | Qoder | `.qoder/skills/` | unsupported | unsupported |
| `qwen-code` | Qwen Code | `.qwen/skills/` | planned | unsupported |
| `replit` | Replit | `~/.config/agents/skills/` | unsupported | unsupported |
| `roo` | Roo Code | `~/.roo/skills/` | unsupported | unsupported |
| `trae` | Trae | `~/.trae/skills/` | unsupported | unsupported |
| `trae-cn` | Trae CN | `.trae/skills/` | unsupported | unsupported |
| `warp` | Warp | `~/.agents/skills/` | unsupported | unsupported |
| `windsurf` | Windsurf | `~/.codeium/windsurf/skills/` | planned | unsupported |
| `zencoder` | Zencoder | `.zencoder/skills/` | unsupported | unsupported |

## Target Details

### Claude Code

- Skills are managed symlinks in `~/.claude/skills/`.
- MCP servers are merged into `~/.claude.json` using the `mcpServers` shape.
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
- **Planned** means Nexus knows the likely native config path, but does not write it until merge semantics are implemented and tested.
- **Unsupported** means Nexus intentionally does not manage that resource for the target today.
