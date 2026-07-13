# Deployment and Platform Contracts

## Review-first lifecycle

For product changes that affect deployment, the supported sequence is:

1. inspect with `nexus audit --redact-home` where applicable;
2. run `nexus sync --dry-run` and review package, hook, MCP, and target effects;
3. run an explicit sync only when deployment itself is in scope and approved;
4. run `nexus doctor` to inspect manifest, cache, lockfile, symlinks, overlays, hooks, and MCP health.

`cmd_sync` validates the manifest before network/filesystem work and uses an ephemeral checkout for dry-run package resolution. `show_review` presents executable MCP commands before deployment.

## Skills and collisions

`Deployer.deploy_skills` deploys skills as symlinks. It may replace an existing symlink but skips an existing non-symlink path. `prune_skills` removes only stale symlinks represented by prior managed state. Generated metadata overlays live under `.nexus/generated/`; never write overlay metadata into immutable package cache snapshots.

## Hooks and MCPs

Follow the semantic ownership rules in [Security and Configuration](security-and-configuration.md). Add regression tests whenever changing target-specific writers, pruning, collision handling, managed markers, deduplication, or secret-preserving merge behavior.

## Product scope versus repository activation

Agent Nexus supports Claude Code, Cursor, Google Antigravity, Codex, and additional skill targets as product behavior in `TARGET_REGISTRY`, docs, examples, and tests. A repository-local Trellis choice to activate only Claude Code and Codex does not remove or narrow those Agent Nexus product capabilities.

Evidence anchors: `nexus.py` `TARGET_REGISTRY`, `cmd_sync`, `cmd_doctor`, `Deployer`; `tests/test_nexus.py`; `docs/targets.md`; `docs/manifest.md`.
