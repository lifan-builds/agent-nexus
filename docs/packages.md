# Package Reference

A Nexus package is a GitHub repository or local directory that contains reusable agent capabilities. Nexus fetches or reads the package, discovers supported assets, deploys the selected assets to target agent tools, and records the result in the lockfile.

## Supported Package Sources

### GitHub repositories

```yaml
packages:
  - repo: lifan-builds/context-harness
    ref: main
```

Nexus resolves the requested `ref` to a commit SHA, fetches the repository, removes its `.git` directory from the cache snapshot, and stores the result under `.nexus/cache/github.com/<owner>/<repo>/<sha>/`.

### Local paths

```yaml
packages:
  - path: ../context-harness
```

Local packages are read directly from disk and are useful while developing a package before publishing it. Local paths are resolved relative to the Agent Nexus repository.

## Discovery Rules

Nexus does not require packages to declare a type. Every package is scanned for every supported asset kind.

| Asset | Discovery rule | Deployment status |
| --- | --- | --- |
| Skills | any directory containing `SKILL.md` | deployed as target skill symlinks |
| Claude hooks | `hooks/hooks.json` or `hooks.json` | copied into repo `.github/hooks/` |
| Cursor hooks | `hooks/hooks-cursor.json` or `hooks-cursor.json` | merged into repo `.cursor/hooks.json` |
| Codex hooks | `hooks/hooks-codex.json` or `hooks-codex.json` | merged into Codex hooks config |
| Commands | Markdown files in `commands/*.md` | discovered and recorded in lockfile |
| Agents | Markdown files in `agents/*.md` | discovered and recorded in lockfile |

Hidden directories are skipped by default, except when they are explicitly included through `sparse_paths`.

## `SKILL.md` Discovery

When a `SKILL.md` file has YAML frontmatter with a `name` field, Nexus uses that value as the skill name. Otherwise it falls back to the containing directory name.

```markdown
---
name: systematic-debugging
---

# Systematic Debugging
```

If a package root itself contains `SKILL.md`, the package name is used as the fallback skill name.

## Filters

### Skills

```yaml
packages:
  - repo: obra/superpowers
    ref: v5.0.4
    skills:
      - systematic-debugging
```

Only listed skills are deployed. If `skills` is omitted, all discovered skills are eligible. If `skills: []`, all skills from that package are disabled. Missing requested skills produce warnings.

The dashboard Inventory controls edit this allowlist directly. Disabled skills can still appear in the dashboard when Nexus can inspect the local package cache, so you can re-enable them without hand-editing YAML.

### Hooks

```yaml
packages:
  - repo: lifan-builds/context-harness
    ref: main
    hooks:
      - codex
```

`hooks: false` or `hooks: []` disables hook deployment for that package.

### Targets

```yaml
packages:
  - repo: obra/superpowers
    ref: v5.0.4
    targets: [claude, cursor]
```

Package targets are intersected with the manifest's top-level targets.

## Target Overlays

Target overlays let you add target-specific metadata without mutating the immutable package snapshot.

```yaml
packages:
  - repo: lifan-builds/context-harness
    ref: main
    skill_overrides:
      context-init:
        skill_frontmatter:
          disable-model-invocation: true
```

For each selected target, Nexus copies the source skill into `.nexus/generated/<target>/skills/<skill>/`, applies the override, and points the target skill symlink to the generated directory.

Supported overlay types today:

- `skill_frontmatter`
- `agents_openai`

## Cache Layout

GitHub package snapshots live under `.nexus/cache/`:

```text
.nexus/cache/github.com/<owner>/<repo>/<commit-sha>/
```

Sparse package snapshots include a sparse-path hash in the cache key:

```text
.nexus/cache/github.com/<owner>/<repo>/<commit-sha>-sparse-<hash>/
```

Marker files named `<cache-key>.fetched` indicate completed fetches.

## Ref Resolution

`ref` can be:

- a branch name, such as `main`
- a tag name, such as `v5.0.4`
- a 40-character commit SHA

Branches and tags are resolved with `git ls-remote` before fetching. The resolved commit SHA becomes the cache key, so deployed symlinks point at a concrete package snapshot.

Pinning tags or commit SHAs is safer than tracking a floating branch when you want reproducible installs.

## Executable Versus Inert Contents

Package contents are inert while cached. They become operational only when Nexus writes target config that refers to them.

Executable or execution-adjacent assets include:

- MCP commands declared in the manifest,
- hook commands from package hook files,
- scripts referenced by those hook commands.

Skill, command, and agent Markdown files are content until a target agent chooses to read or invoke them.

Use `python nexus.py sync --dry-run` to review the MCP commands and target deployment plan before writing target config.

## Lockfile Records

After a real sync, the lockfile records package metadata such as:

- package name,
- resolved cache path,
- discovered skills, hooks, commands, and agents,
- targets that received the package,
- generated overlay paths,
- managed MCP names.

This lets you trace a deployed target skill back to the package snapshot and manifest that installed it.

## Inspect Before Syncing

Recommended review flow:

```bash
python nexus.py sync --dry-run
python nexus.py list
python nexus.py doctor
```

For GitHub packages, you can also inspect the cached package snapshot under `.nexus/cache/` after a dry run resolves packages for discovery. Dry runs do not write target IDE config or lockfiles.
