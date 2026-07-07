# Demo Before And After

This page describes the flagship demo state without relying on private local paths or secrets.

## Before Nexus

A typical multi-agent workspace has the same capability configured several times:

| Surface | Before |
| --- | --- |
| Claude Code skills | manually copied or symlinked into `~/.claude/skills/` |
| Cursor skills | separate skill directory with no shared traceability |
| Antigravity skills | another target-specific skill location |
| Codex skills | separate `~/.codex/skills/` tree |
| MCP servers | repeated JSON/TOML entries across target config files |
| Hooks | target-specific files with unclear ownership |
| Package provenance | whatever the install notes or git history remember |
| Verification | manual spot checks after setup |

Typical questions are hard to answer:

- Which package installed this skill?
- Which commit did this package come from?
- Which MCP command will be registered before I approve it?
- Which hook commands are managed and which are mine?
- Did every target actually receive the same capability?

## After Nexus

A Nexus-managed workspace has one manifest, a review step, native target files, and a lockfile.

| Surface | After |
| --- | --- |
| Manifest | `nexus.personal.yml` or committed `nexus.yml` declares targets, packages, MCPs, and overlays |
| Audit | `python nexus.py audit` inventories existing target config before writes |
| Dry run | `python nexus.py sync --dry-run` shows MCP and hook commands plus deploy plan |
| Sync | `python nexus.py sync` writes target-native config after confirmation |
| Lockfile | `nexus.personal.lock.yml` records package source metadata, discovered assets, targets, overlays, hooks, and managed MCP names |
| Doctor | `python nexus.py doctor` checks manifest, cache, lockfile, skills, MCP config, overlays, and hooks |

## Demo Narrative

1. Run `python nexus.py audit --redact-home` to show what already exists.
2. Run `python nexus.py init` to create a personal manifest if needed.
3. Edit the manifest to include Context Harness, target list, and MCP servers.
4. Run `python nexus.py sync --dry-run`.
5. Point out the MCP security review.
6. Point out the hook review and target deploy plan.
7. Run `python nexus.py sync` after approval.
8. Open the lockfile and show package source metadata and target deployments.
9. Run `python nexus.py doctor`.
10. Show one target skill symlink and one target MCP config entry as proof.

## Screenshot-Friendly Proof Points

Use sanitized or redacted paths in public screenshots:

- `~/.claude/skills/context-harness -> .nexus/cache/.../context-harness/...`
- `~/.cursor/mcp.json` contains a managed MCP server while unrelated servers remain.
- `~/.codex/config.toml` contains a Nexus managed MCP block and preserves surrounding config.
- `nexus.personal.lock.yml` contains package source metadata and hook deployments.
- `doctor` reports healthy skill symlinks and MCP server counts.
