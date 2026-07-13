# Agent Nexus Engineering Specifications

These specifications describe the tracked Agent Nexus repository and its product behavior. They do not authorize reading or changing ignored personal manifests, credentials, user-global agent configuration, or `.nexus/` runtime state.

## Pre-Development Checklist

1. Classify paths with [Repository Ownership](repository-ownership.md).
2. Preserve personal values and unmanaged configuration according to [Security and Configuration](security-and-configuration.md).
3. For deployment behavior, use [Deployment and Platform Contracts](deployment-and-platforms.md) and the linked product documentation/source.
4. Keep local Trellis activation separate from Agent Nexus product support for other platforms and Context Harness as described in [Context and Product Boundaries](context-and-product-boundaries.md).
5. Select checks from [Verification](verification.md). Do not invent lint, typecheck, database, or architecture rules that the repository does not define.

## Topics

- [Repository Ownership](repository-ownership.md) — authoritative source, generated, runtime, and historical paths.
- [Security and Configuration](security-and-configuration.md) — personal-manifest precedence, secrets, and merge boundaries.
- [Deployment and Platform Contracts](deployment-and-platforms.md) — preview/deploy/doctor flow, skills, hooks, and MCP behavior.
- [Context and Product Boundaries](context-and-product-boundaries.md) — Trellis ownership and preserved product capabilities.
- [Verification](verification.md) — repository-native commands and isolation requirements.

## Quality Check

Before completing a change:

- verify only intended tracked source/documentation and approved project-local generated activation changed;
- verify no personal manifest, lock, credential, `.nexus/`, browser session, dependency cache, or build artifact was staged;
- run the applicable checks in [Verification](verification.md), reporting skips and failures accurately;
- run `python3 ./.trellis/scripts/get_context.py --mode packages` and confirm this `agent-nexus` layer is discoverable;
- preserve Agent Nexus product support for Cursor, Antigravity, Context Harness, and other targets unless product behavior is explicitly in scope.
