# Security and Configuration

## Personal precedence and exclusion

`Config._resolve_manifest_path` in `nexus.py` chooses `nexus.personal.yml` when present and otherwise uses `nexus.yml`; `_resolve_lockfile_path` applies the matching lockfile. Personal manifests, locks, local credentials, and values derived from them must remain ignored and must not be quoted in specs, tests, task evidence, logs, or commits.

Use placeholders in tracked examples. Tests that need personal configuration must create neutral fixtures under temporary directories. Never use the contributor's real `HOME`, `CODEX_HOME`, or agent configuration.

## Merge ownership

- JSON MCP sync preserves existing server keys by merging rather than replacing local values (`Deployer._sync_mcps_for_target` and `_merge_mcp_entry`).
- Codex MCP sync owns only the `BEGIN/END NEXUS MANAGED MCP SERVERS` block and preserves content outside it (`_sync_mcps_for_codex`, `_strip_codex_managed_block`).
- Codex hook sync strips only commands marked `--nexus-package`, preserves unmanaged entries, substitutes package roots, and deduplicates (`_merge_codex_hooks`).
- Cursor product hooks are merged and deduplicated by normalized content (`_merge_hooks`). Claude product hook filename collisions or unverified overwrites fail closed (`deploy_hooks`).

These are Agent Nexus product contracts. They do not authorize running sync against ignored personal/global state during unrelated repository maintenance.

## Review rules

Before staging, inspect path names and tracked diffs for credentials, environment values, private package names, absolute personal paths, browser/session data, key/certificate files, and generated runtime state. A narrow ignore pattern is not proof that a diff is safe.

Evidence anchors: `nexus.py` `Config`, `Deployer.deploy_hooks`, MCP merge methods, dashboard redaction helpers; `tests/test_nexus.py`; `docs/security-model.md`; `docs/mcp.md`; `docs/hooks.md`.
