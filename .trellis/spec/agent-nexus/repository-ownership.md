# Repository Ownership

## Authoritative tracked source

- `nexus.py` is the supported Python CLI and behavioral source.
- `tests/` records executable contracts; `docs/`, `README.md`, `CONTRIBUTING.md`, and checked-in examples document public behavior.
- `nexus.example.yml` is the public manifest template. It is not the active personal manifest.
- `.trellis/spec/agent-nexus/` holds durable repository engineering guidance. `.trellis/tasks/` holds task-local plans and evidence.

## Generated and runtime paths

- `.nexus/` is mutable cache/generated deployment state, not source. Package cache snapshots are content-addressed; generated skill overlays are reproducible outputs.
- Personal manifests and lockfiles (`nexus.personal.yml`, `nexus.personal.lock.yml`, and local `nexus.yml`/`nexus.lock.yml` where ignored) are machine state, not tracked examples.
- `.claude/` and `.codex/` contain project-local agent adapters/configuration. Treat settings files as semantic configuration, not replaceable blobs.
- `.agents/skills/` is the shared project-local Trellis skill surface required by Codex.
- Tracked `build/` and `agent_nexus.egg-info/` entries are existing generated artifacts. Do not hand-edit or opportunistically clean them; run builds in a disposable worktree.

## Historical and planning material

Long-running product history belongs in `CHANGELOG.md`, `PLANS.md`, `FINDINGS.md`, and focused product documents. Do not recreate a second active context owner beside Trellis or turn transient handoff state into durable specification.

Evidence anchors: `nexus.py` (`Config`, `PackageManager`, `Deployer`, `generate_lockfile`), `CONTRIBUTING.md`, `.gitignore`, and `docs/package-trust.md`.
