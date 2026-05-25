# Agent Domain Docs

This repo uses a single-context domain-doc layout.

`CONTEXT.md` at the repository root is the canonical project memory. Matt Pocock's engineering skills should read it for project language, architectural constraints, workflow expectations, and durable lessons.

`NOW.md` is short-lived session state maintained by context-harness. Use it for recovery, not durable decisions.

`PLAN.md` is task-local planning state. Use it when a multi-step task is active.

Architectural decisions should live under `docs/adr/` if they are hard to reverse, surprising later, and involve a real trade-off. If no ADR exists for an area, do not infer one from surrounding prose.

Do not create a separate Matt-specific context file. Context-harness owns the project memory files; Matt's skills consume them.
