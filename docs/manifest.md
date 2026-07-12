# Manifest Reference

A Nexus manifest declares the packages, MCP servers, and targets that should be managed for an agent workspace.

## File Precedence

Nexus looks for manifests in this order:

1. `nexus.personal.yml`
2. `nexus.yml`

Use `nexus.personal.yml` for machine-specific setup and secrets-adjacent placeholders. It is gitignored by this repository. Use `nexus.yml` when a team wants to commit shared packages, targets, and MCP names.

The lockfile follows the active manifest:

- `nexus.personal.yml` writes `nexus.personal.lock.yml`
- `nexus.yml` writes `nexus.lock.yml`

## Top-Level Fields

### `name`

Human-readable name for the workspace.

```yaml
name: my-agent-workspace
```

### `version`

Manifest version for humans and future tooling. Nexus does not currently enforce semantic versioning.

```yaml
version: 1.0.0
```

### `targets`

Targets that receive managed skills, MCP config, and supported hooks.

```yaml
targets:
  - claude
  - cursor
  - antigravity
  - codex
```

If `targets` is omitted, Nexus defaults to the four core native targets: `claude`, `cursor`, `antigravity`, and `codex`. Use `targets: ["*"]` to deploy skills to every skills target preset. Nexus currently includes 41 skills presets; only the core targets have tested MCP writers and hook support where listed in `docs/targets.md`.

Common aliases such as `claude-code`, `google-antigravity`, `openai-codex`, `hermes-agent`, `qwen`, `roo-code`, `copilot`, `kilo`, and `open-code` are canonicalized to target keys. Unknown targets are rejected with an actionable validation error so typos cannot become silent no-ops.

## Packages

Packages provide skills, hooks, commands, and agents. Nexus auto-discovers all supported assets instead of requiring a package type.

### GitHub package

```yaml
packages:
  - repo: lifan-builds/context-harness
    ref: main
```

- `repo` uses `owner/name` syntax.
- `ref` can be a branch, tag, or 40-character commit SHA.
- GitHub packages are cached under `.nexus/cache/github.com/<owner>/<repo>/<resolved-sha>/`.

### Local package

```yaml
packages:
  - path: ../context-harness
```

Local packages are useful for development and pre-release validation. Their paths are resolved relative to the Agent Nexus repository.

### Package target filter

Limit a package to selected manifest targets:

```yaml
packages:
  - repo: obra/superpowers
    ref: v5.0.4
    targets: [claude, cursor]
```

Package-level `targets` cannot add a target that is not listed in the top-level `targets` section.

### Skill filter

Deploy only selected discovered skills from a package:

```yaml
packages:
  - repo: obra/superpowers
    ref: v5.0.4
    skills:
      - systematic-debugging
      - verification-before-completion
```

If `skills` is omitted, all discovered skills are eligible for deployment. If `skills` is a list, only those skills are eligible. If `skills: []`, no skills from that package are deployed. If a requested skill is not discovered, Nexus prints a warning and continues with the skills it did find.

The dashboard Inventory controls write this same allowlist when you enable or disable package skills.

### Hook filter and disable behavior

Deploy only selected hook assets from a package:

```yaml
packages:
  - repo: lifan-builds/context-harness
    ref: main
    hooks:
      - codex
```

Disable package hook deployment entirely:

```yaml
packages:
  - repo: lifan-builds/context-harness
    ref: main
    hooks: false
```

`hooks: []` also disables hooks for that package. If `hooks` is omitted, all discovered hook assets for configured targets are eligible for deployment.

### Sparse paths

Fetch selected paths from a large GitHub package:

```yaml
packages:
  - repo: pbakaus/impeccable
    ref: main
    sparse_paths:
      - .agents/skills/impeccable
```

Sparse package caches include a hash of the sparse path list so different sparse selections do not collide.

## Skill Overrides

`skill_overrides` generate target-specific skill copies under `.nexus/generated/<target>/skills/<skill>/`. This keeps package snapshots immutable while allowing target metadata changes.

### Skill frontmatter override

```yaml
packages:
  - repo: lifan-builds/context-harness
    ref: main
    skill_overrides:
      context-init:
        skill_frontmatter:
          disable-model-invocation: true
```

### Codex/OpenAI agent metadata override

```yaml
packages:
  - repo: obra/superpowers
    ref: v5.0.4
    skill_overrides:
      systematic-debugging:
        targets: [codex]
        agents_openai:
          interface:
            display_name: Systematic Debugging
            short_description: Use this debugging workflow when explicitly invoked.
          policy:
            allow_implicit_invocation: false
```

If `targets` is omitted inside a skill override, the override applies to all targets selected for that package.

The dashboard's manual-invocation-only toggle writes both `skill_frontmatter.disable-model-invocation: true` and `agents_openai.policy.allow_implicit_invocation: false` for broad target compatibility. Clearing the toggle removes only those manual-only markers and preserves unrelated override metadata.

## MCP Servers

### Stdio MCP

```yaml
mcps:
  - name: context7
    command: npx
    args: ["-y", "@upstash/context7-mcp@latest"]
```

Nexus resolves `npx` and `node` to an absolute command path when possible and adds a standard `PATH` env value if one is not provided.

### SSE MCP

```yaml
mcps:
  - name: docs
    transport: sse
    url: https://example.com/mcp
```

JSON targets receive `type: sse` and `url`. Codex receives `type = "sse"` and `url`. Antigravity receives `serverUrl`.

### HTTP MCP

```yaml
mcps:
  - name: memory
    transport: http
    url: https://example.com/mcp
```

JSON targets receive `type: http` and `url`. Codex receives `url`. Antigravity receives `serverUrl`.

### Env placeholders

Use placeholders instead of committing secrets:

```yaml
mcps:
  - name: github
    command: npx
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_TOKEN: "${GITHUB_TOKEN}"
```

When the target config already has a real local value for the same env key, Nexus preserves that local value instead of replacing it with the placeholder. Nexus also preserves local-only env keys that are not mentioned by the manifest.

### Headers and OAuth metadata

URL-based MCPs may include headers and OAuth resource metadata:

```yaml
mcps:
  - name: remote-docs
    transport: http
    url: https://example.com/mcp
    oauth_resource: https://example.com/
    headers:
      X-Team: agents
```

Treat header values like secrets if they contain tokens. The dashboard redacts header values before showing manifest state.

## Optional MCPs

Optional MCPs are prompted interactively during sync, or included automatically with `sync --all`.

```yaml
optional_mcps:
  - name: github-mcp
    command: npx
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_TOKEN: "${GITHUB_TOKEN}"
    description: GitHub API access
```

You can also mark an entry in `mcps` as optional:

```yaml
mcps:
  - name: github-mcp
    command: npx
    args: ["-y", "@modelcontextprotocol/server-github"]
    optional: true
    description: GitHub API access
```

Skipped optional MCPs are not written to the lockfile as managed MCPs, so Nexus will not prune a server that it never accepted for deployment. If an optional MCP was managed by the previous lockfile and is skipped on the next sync, Nexus treats it as stale and prunes it from target configs.

## Examples

### Individual setup

```yaml
name: personal-agent-stack
version: 1.0.0
targets: [claude, cursor, antigravity, codex]
packages:
  - repo: lifan-builds/context-harness
    ref: main
    hooks: [codex]
mcps:
  - name: context7
    command: npx
    args: ["-y", "@upstash/context7-mcp@latest"]
optional_mcps:
  - name: playwright
    command: npx
    args: ["-y", "@playwright/mcp@latest"]
    description: Isolated, reproducible browser automation; enable only when needed
```

### Team setup

```yaml
name: team-agent-stack
version: 1.0.0
targets: [claude, cursor]
packages:
  - repo: your-org/agent-skills
    ref: v1.2.0
mcps:
  - name: github
    command: npx
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_TOKEN: "${GITHUB_TOKEN}"
```

Commit shared package names and env placeholder keys. Do not commit real secret values.

### MCP-only setup

```yaml
name: mcp-only
version: 1.0.0
targets: [claude, cursor, codex]
packages: []
mcps:
  - name: context7
    command: npx
    args: ["-y", "@upstash/context7-mcp@latest"]
```

### Package-only setup

```yaml
name: package-only
version: 1.0.0
targets: [claude, cursor]
packages:
  - repo: obra/superpowers
    ref: v5.0.4
    skills:
      - systematic-debugging
mcps: []
```
