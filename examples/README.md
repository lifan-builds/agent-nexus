# Example manifests

- [`minimal.yml`](minimal.yml) — smallest package-oriented starting point.
- [`context-harness.yml`](context-harness.yml) — Context Harness with review-first MCP policy.
- [`mcp-only.yml`](mcp-only.yml) — MCP management without packages.
- [`team.yml`](team.yml) — shared team targets and optional capabilities.
- [`package-overlays.yml`](package-overlays.yml) — target-specific skill metadata overlays.

For a brand-new workspace, prefer `nexus init`. It creates an empty personal manifest. Copy an example only after reviewing every package, MCP command, hook, target, and secret placeholder.
