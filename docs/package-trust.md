# Package Trust And Lockfile Traceability

Agent Nexus is designed around a simple trust boundary: package contents are fetched or read for discovery, executable changes are surfaced before target config is written, and a lockfile records what landed after sync.

## Supported Package Sources

Agent Nexus supports two package sources today:

- GitHub repositories declared with `repo: owner/name`
- local directories declared with `path: ../relative/path`

GitHub packages are resolved to commit snapshots and cached under `.nexus/cache/`. Local packages are read directly from disk for development or pre-release validation.

## What `ref` Means

For GitHub packages, `ref` is the requested Git reference:

```yaml
packages:
  - repo: lifan-builds/context-harness
    ref: main
```

`ref` may be:

- a branch, such as `main`,
- a tag, such as `v1.2.3`,
- a full 40-character commit SHA.

Nexus resolves branch and tag refs with `git ls-remote`, then uses the resolved commit SHA as the package cache key.

## Why Pin Tags Or SHAs

Floating branches such as `main` are convenient while iterating, but their contents can change between syncs. Tags and commit SHAs are better for reproducible agent workspaces because reviewers can inspect the exact package version before adopting it.

Recommended pattern:

- use `main` only for packages you actively develop or intentionally track,
- use a release tag for normal shared setups,
- use a commit SHA for high-sensitivity environments.

## How GitHub Refs Resolve

When a GitHub package is fetched, Nexus:

1. checks whether `ref` is already a 40-character SHA,
2. otherwise runs `git ls-remote` against the repository and requested ref,
3. falls back to checking `refs/tags/<ref>`,
4. clones the package at the requested ref,
5. falls back to fetching the resolved SHA if the direct clone fails,
6. removes `.git` from the cached snapshot.

The resolved snapshot is stored under:

```text
.nexus/cache/github.com/<owner>/<repo>/<commit-sha>/
```

Sparse checkouts include a suffix derived from the sparse path list:

```text
.nexus/cache/github.com/<owner>/<repo>/<commit-sha>-sparse-<hash>/
```

## Does Discovery Run Package Code?

Nexus package discovery does not execute package code. It walks files and parses known configuration surfaces:

- `SKILL.md` files for skills,
- hook JSON files,
- Markdown files in `commands/`,
- Markdown files in `agents/`.

Discovery may read package files and parse YAML/JSON metadata, but package scripts are not run during discovery.

## What Can Become Executable?

Package files become operational only after a sync writes target config or target symlinks.

Execution-relevant surfaces include:

- MCP commands declared in the manifest,
- hook commands declared by package hook JSON,
- scripts referenced by those hook commands,
- target agents reading deployed skill content during later agent sessions.

Nexus treats MCP commands as the highest-risk config surface and shows them in the sync security review. Hooks are also execution-relevant; review package hook files before syncing packages you do not already trust.

## Dry Run Review

Use dry run before a first sync or after changing packages:

```bash
python nexus.py sync --dry-run
```

Dry run may fetch packages into `.nexus/cache/` so Nexus can discover assets, but it exits before writing target IDE config or lockfiles. It prints:

- MCP commands and URL transports that would be registered,
- skills that would be deployed and to which targets,
- generated overlay types,
- hook targets that would be managed.

Stop after dry run if an MCP command, package source, hook source, or target path is unexpected.

## Lockfile Traceability

A real sync writes `nexus.personal.lock.yml` when using `nexus.personal.yml`, otherwise `nexus.lock.yml`.

The lockfile currently records:

- lockfile version,
- generation time,
- Nexus version,
- manifest path used for the sync,
- package name,
- package source type,
- GitHub repo, source URL, requested ref, resolved commit, sparse paths, and cache path where applicable,
- local package path and resolved path where applicable,
- resolved package/cache path,
- discovered skills, hooks, commands, and agents,
- target deployment list,
- hook deployment targets,
- generated overlay paths,
- managed MCP names,
- accepted optional MCPs,
- warnings for floating refs such as `main`.

This supports the core launch promise:

> Review before write. Trace after sync.

## Current Lockfile Limits

The current lockfile does not yet record every trust detail in the roadmap. Planned improvements include recording:

- package content hash summaries,
- previous lockfile comparison summaries.

Until those land, use the source metadata, package cache path, and manifest to correlate a package back to its source.

## Manual Package Review

A cautious review flow:

```bash
python nexus.py sync --dry-run
find .nexus/cache -name SKILL.md -print
python nexus.py list
python nexus.py doctor
```

For a specific cached package, inspect:

- `SKILL.md` files,
- `hooks/hooks.json`, `hooks/hooks-cursor.json`, and `hooks/hooks-codex.json`,
- scripts referenced by hook commands,
- `commands/*.md`,
- `agents/*.md`.

Prefer pinned tags or SHAs when sharing manifests with a team.

## Planned CLI Helpers

The roadmap tracks future commands for making package and lockfile inspection easier:

```bash
python nexus.py package inspect <package-name-or-repo>
python nexus.py package list
python nexus.py lock show
python nexus.py lock diff
```

These commands are not implemented yet. Today, use `sync --dry-run`, `list`, `doctor`, the lockfile, and the package cache for inspection.
