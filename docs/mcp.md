# MCP Configuration

Agent Nexus manages MCP server declarations across Claude Code, Cursor, Google Antigravity, and Codex from the manifest. Its MCP behavior is designed to be reviewable and non-destructive.

## Manifest Schema

### Stdio servers

```yaml
mcps:
  - name: context7
    command: npx
    args: ["-y", "@upstash/context7-mcp@latest"]
```

If `command` is omitted, Nexus defaults to `npx`. For `npx` and `node`, Nexus resolves the command to an absolute path when possible. When `env` is omitted, Nexus adds a standard PATH value for restricted agent environments; explicit `env: {}` preserves an empty environment mapping.

### SSE URL servers

```yaml
mcps:
  - name: docs
    transport: sse
    url: https://example.com/mcp
```

### HTTP URL servers

```yaml
mcps:
  - name: memory
    transport: http
    url: https://example.com/mcp
```

The roadmap calls this category StreamableHTTP in some places. The current manifest value used by Nexus is `transport: http`.

### Env values

```yaml
mcps:
  - name: github
    command: npx
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_TOKEN: "${GITHUB_TOKEN}"
```

Use placeholders for secrets. When an existing target config has a real value for the same env key and the manifest value is a placeholder, Nexus keeps the existing local value.

### URL headers and OAuth resource

```yaml
mcps:
  - name: remote-docs
    transport: http
    url: https://example.com/mcp
    oauth_resource: https://example.com/
    headers:
      X-Team: agents
```

Headers are copied into supported target config shapes. Treat header values as sensitive if they contain tokens.

## Per-MCP Target Filters

Use `targets` on an MCP declaration to deploy it only to selected top-level targets:

```yaml
mcps:
  - name: local-browser
    command: /absolute/path/to/launcher
    args: []
    env: {}
    targets: [claude, cursor, antigravity]
```

The filter is canonicalized and intersected with the manifest's top-level targets. Omitting it preserves the original behavior and deploys the server to every configured target with an implemented MCP writer. `targets: []` deploys nowhere. Unknown or MCP-unsupported names and duplicate canonical targets fail manifest validation.

The lockfile records the resolved target list for every managed MCP. On a later sync, removing a target from one MCP prunes that previously managed server only from the newly excluded host; unrelated and unmanaged servers remain intact. The dry-run and security review print each MCP's resolved target list so a scope change is visible before deployment.

Package-level `targets` remains independent: it filters discovered package assets such as skills and does not affect a separate MCP declaration. Likewise, MCP target filters select hosts rather than repositories.

For an absolute launcher that must preserve an empty environment mapping, declare `env: {}` explicitly. Omitting `env` retains Nexus's standard PATH injection for restricted agent environments.

## Browser Tooling Policy

Use one browser or desktop-control path for each job. Prefer built-in web retrieval for static research; use a pinned existing-profile browser MCP such as Playwriter only for dynamic/authenticated work in an explicitly selected task-owned page; keep Chrome DevTools task-local for bounded diagnostics; and use the selected host's native controller only when the browser layer is insufficient. Per-MCP target filters place vanilla Open Computer Use on Claude Code, Cursor, and Antigravity while leaving Codex on its native computer-use capability. Retired Peekaboo and Kimi WebBridge remain absent from the manifest, managed targets, package/runtime state, and active routing; restoring either requires a fresh explicit installation and security review.

Reusable browser or native MCPs may be Nexus-managed with explicit per-MCP targets, while project-only diagnostics stay in native target configuration. Preserve each controller's upstream command, selected-page or native-permission contract, and rollback procedure; a target filter narrows host deployment but does not narrow runtime authority. Do not infer or add a wrapper, VM, app allowlist, or environment policy merely from host filtering. Never run multiple controllers against the same state merely because multiple hosts can discover them.

**Playwright MCP** belongs under `optional_mcps` for isolated, reproducible browser automation and end-to-end testing.

When Playwright was managed by a previous sync and is declined later, it is omitted from the accepted MCP set and pruned using the previous lockfile.

## Repository-Scoped MCPs

Agent Nexus can filter an MCP by target host, but it does not filter an individual MCP by repository. A package-level `targets` filter affects package assets such as skills rather than MCP deployment.

Capabilities that must exist only inside one repository therefore belong in the host's native project configuration, not the shared Nexus manifest:

| Capability | Owning repository | Project scope |
| --- | --- | --- |
| `nitan` | `/Users/lfan/Project/agent` | `.mcp.json`, `.cursor/mcp.json`, `.agents/mcp_config.json`, and `.codex/config.toml` |
| `robinhood-trading` | `/Users/lfan/Project/moonshot` | The same four native project surfaces, using the public Robinhood endpoint |

Nitan credentials remain in a permission-restricted external file loaded by the Agent repository's launcher. Robinhood OAuth/session state remains host-owned and external. Do not add either server back to shared `mcps` as a fallback for project approval, repository trust, unavailable host CLIs, or OAuth limitations.

To migrate or roll back this boundary, review name-only previous-lock and target inventories before the normal `sync --dry-run` → `sync --yes` → `doctor` sequence. Restore global declarations first during rollback, then remove project entries; never hand-edit generated global target files.

## Per-Target Output Formats

### Claude Code

Path: `~/.claude.json`

Stdio output shape:

```json
{
  "mcpServers": {
    "context7": {
      "type": "stdio",
      "command": "/path/to/npx",
      "args": ["-y", "@upstash/context7-mcp@latest"],
      "env": {"PATH": "..."}
    }
  }
}
```

URL output shape:

```json
{
  "mcpServers": {
    "docs": {
      "type": "sse",
      "url": "https://example.com/mcp"
    }
  }
}
```

### Cursor

Path: `~/.cursor/mcp.json`

Cursor uses the same `mcpServers` JSON shape as Claude Code in the current Nexus implementation.

### Google Antigravity

Path: `~/.gemini/antigravity/mcp_config.json`

Stdio output uses the normal `mcpServers` JSON shape. URL-based MCPs use Antigravity's `serverUrl` shape:

```json
{
  "mcpServers": {
    "docs": {
      "serverUrl": "https://example.com/mcp"
    }
  }
}
```

If headers are present, Nexus includes them as `headers`.

### Codex

Path: `~/.codex/config.toml`

Nexus writes MCP servers only inside a managed TOML block:

```toml
# BEGIN NEXUS MANAGED MCP SERVERS
# This block is generated by agent-nexus. Edit nexus.personal.yml instead.

[mcp_servers."context7"]
command = "/path/to/npx"
args = ["-y", "@upstash/context7-mcp@latest"]

[mcp_servers."context7".env]
PATH = "..."
# END NEXUS MANAGED MCP SERVERS
```

SSE output includes `type = "sse"` and `url`. HTTP output uses `url` without `type = "sse"`.

## Non-Destructive Merge Semantics

For JSON targets, Nexus:

- creates the `mcpServers` object if missing,
- adds manifest-managed MCP servers,
- updates managed command, args, URL, type, headers, and OAuth resource fields,
- preserves unmanaged MCP servers not declared in the manifest,
- preserves local-only top-level Claude Code state and keys on existing server entries,
- preserves local env values when the manifest uses placeholders,
- preserves local-only env keys not mentioned by a non-empty manifest mapping, and
- treats explicit `env: {}` as a complete empty shape, clearing stale env keys on that managed server.

For Codex, Nexus:

- preserves content outside the managed block,
- rewrites the managed block from the accepted manifest MCP list,
- preserves placeholder env values from the existing managed block,
- prunes stale managed MCP sections from the previous lockfile.

JSON files are rewritten with two-space indentation. TOML content inside the Codex managed block is regenerated by Nexus.

## Managed And Unmanaged Entries

Nexus treats MCPs listed in the active manifest and accepted optional MCPs as managed for that sync. The lockfile records each managed MCP name and its resolved target list after a real sync.

Unmanaged entries are existing target config entries not listed in the manifest or lockfile-managed set. Nexus preserves them during normal sync.

Skipped optional MCPs are not recorded as managed, so Nexus will not prune a server that it never accepted for deployment. If the previous lockfile records an optional MCP as managed and the next sync skips it, Nexus treats it as stale and prunes it.

## Stale Managed MCP Pruning

When a previous lockfile says Nexus managed an MCP, and the current accepted manifest no longer includes it for a target, Nexus removes that stale managed MCP from that target config. This covers both full removal and per-MCP target contraction.

For JSON targets, it deletes the stale server key from `mcpServers` only on affected hosts.

For Codex, it removes the stale section only from the Nexus managed TOML block.

## Security Review Output

Before writing MCP config, `nexus sync` prints the commands or URLs that will be registered:

```text
==> Security review - MCP servers to be registered:

    context7                       stdio: npx -y @upstash/context7-mcp@latest -> claude,cursor,antigravity,codex
    docs                           sse: https://example.com/mcp -> claude,cursor
```

Without `--yes`, Nexus asks for confirmation before applying a real sync. `sync --dry-run` prints the same review and exits before writing target config or lockfiles.

## Current Limitations

- Native target validation of remote MCP URL auth flows is outside the current CLI.
- JSON target files are preserved semantically but not byte-for-byte; Nexus rewrites JSON with two-space indentation.
- Transport docs use `transport: http` for the current implementation even when external ecosystems call the transport StreamableHTTP.
