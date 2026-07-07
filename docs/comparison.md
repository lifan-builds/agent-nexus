# Comparison Guide

Agent Nexus is not trying to replace every agent setup tool. Choose based on the workflow you want.

## Short Version

| Tooling style | Best fit |
| --- | --- |
| Agent Nexus | Reviewable package workflow across Claude Code, Cursor, Google Antigravity, and Codex |
| AGHub-style hub | Broad target coverage and hub-style MCP/skill management |
| GAAL-style machine sync | Reproducible machine setup, dotfiles/content sync, and polished audit onboarding |
| Native plugin systems | Platform-specific discovery, first-party UX, and target-specific capabilities |

## Agent Nexus vs AGHub

AGHub's public positioning emphasizes breadth: a hub for many AI coding agents, MCP management, and portable skill-style packages.

Agent Nexus optimizes for a narrower workflow:

- install GitHub or local agent packages,
- preview executable MCP commands before writing target config,
- deploy native target files for the agent tools this repo tests,
- preserve unmanaged config during merges,
- record package snapshots and deployed resources in a lockfile,
- verify the result with `doctor`.

Choose AGHub-style tooling when target breadth and hub discovery matter most. Choose Agent Nexus when you want package snapshots, target overlays, dry-run review, and lockfile traceability for the coding agents you actually use.

## Agent Nexus vs GAAL

GAAL's public positioning emphasizes reproducible setup from one YAML across machines, including audit/init/sync onboarding, dotfiles or content sync, and local-first machine configuration.

Agent Nexus is more package-oriented:

- packages can contain skills, hooks, commands, and agents,
- MCP declarations live beside package selections,
- target overlays customize package metadata without mutating package snapshots,
- sync writes native target config and a traceable lockfile.

Choose GAAL-style tooling when your main goal is whole-machine or dotfiles-style reproducibility. Choose Agent Nexus when your main goal is installing and reviewing agent capabilities as packages.

## Agent Nexus vs Native Plugin Systems

Native plugin systems are usually best for one target at a time. They can provide first-party UX, platform-specific validation, and ecosystem discovery that a cross-target tool should not duplicate.

Agent Nexus is useful when the same capability should be kept consistent across multiple targets:

- the same MCP server in several config formats,
- the same skill package linked into multiple skill directories,
- hooks installed only for targets that support them,
- one lockfile showing what landed.

Use native tooling for platform-specific marketplace workflows. Use Agent Nexus for cross-agent consistency, review, and traceability.

## What Agent Nexus Does Not Claim

Agent Nexus does not claim to support the most agent targets. It currently focuses on Claude Code, Cursor, Google Antigravity, and Codex.

Agent Nexus does not claim to be a generic dotfiles manager. It manages agent workspace capabilities: packages, MCP servers, skills, hooks, overlays, and lockfiles.

Agent Nexus does not claim competitors lack specific features unless their current public docs or source have been rechecked in the same work session.

## Positioning Sentence

Agent Nexus is the safe package manager for your agent workspace: install agent capabilities from GitHub, review executable changes before they touch local config, deploy native target files, and trace the result with a lockfile and doctor.
