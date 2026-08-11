# Agent Nexus retirement

Agent Nexus was retired on 2026-08-11 because Codex is the only supported active host.

The repository is preserved at `/Users/lfan/Project/archive/agent-nexus` as historical rollback material. Native Codex user/project configuration and owning-repository `.agents/skills` are the current authorities. The archived manifest, generated state, and lockfile are not an active deployment source.

Rollback is reconstruction-based: move this repository back to `/Users/lfan/Project/agent-nexus`, recreate only the exact `~/.local/bin/nexus` link after verifying its target, review `nexus sync --dry-run`, apply once only if the preview is exact, then run `nexus doctor`. Restore native Codex declarations only after ownership is re-established. Never copy or record personal-manifest values.
