# Agent Domain Docs

This repository uses Trellis as its single project-local context and task owner.

Durable Agent Nexus engineering rules live under `.trellis/spec/agent-nexus/`. Trellis task artifacts hold task-local requirements, plans, evidence, and handoff state; long-running product history remains in `PLANS.md`, `FINDINGS.md`, and focused documentation.

Architectural decisions should live under `docs/adr/` if they are hard to reverse, surprising later, and involve a real trade-off. If no ADR exists for an area, do not infer one from surrounding prose.

Do not create a separate Matt-specific context file. Matt Pocock's engineering skills should consume the relevant Trellis specifications and task context. Context Harness remains a supported Agent Nexus package for deployment to other repositories, but it does not own this repository's local context.
