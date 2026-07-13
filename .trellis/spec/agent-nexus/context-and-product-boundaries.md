# Context and Product Boundaries

## Active repository context

Trellis is the sole project-local activation and task-context owner through `AGENTS.md`, `.trellis/workflow.md`, `.trellis/spec/`, and `.trellis/tasks/`. Do not add a competing generated block to `AGENTS.md` or restore obsolete repository-local Context Harness source/index/runtime files.

Project-local Trellis adapters are intentionally limited to Claude Code and Codex, plus the shared `.agents/skills/` surface required by Codex. Obsolete repository-local Cursor and generic Antigravity Trellis activation directories must remain absent so Trellis 0.6.6 directory detection does not regenerate those adapters.

## Preserved Agent Nexus product functionality

Context Harness remains a supported external Agent Nexus package. Preserve:

- package examples and public documentation that describe fetching, discovery, deployment, locking, and verification;
- `scripts/context-index.js`, `scripts/context-gen.js`, and `scripts/lib.js` as product tooling/history while they remain referenced and tested;
- Context Harness fixtures and tests in `tests/test_nexus.py`;
- changelog, plans, findings, and competitive documents when references are historical or describe product capability.

Removing obsolete local activation is not permission to delete Cursor, Antigravity, Context Harness, or multi-target behavior from Agent Nexus product code.

## Transient state

Use Trellis task artifacts and workspace journals for current focus, blockers, implementation evidence, and handoff. Do not create root-level transient context files or regenerate `.context-harness/` retrieval output for this repository.

Evidence anchors: `AGENTS.md`, `.trellis/workflow.md`, `README.md` Context Harness example, `examples/context-harness.yml`, `nexus.example.yml`, Context Harness tests, and the context scripts.
