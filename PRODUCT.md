# Product

## Register

product

## Users

Developers and agent-workspace maintainers who manage skills, MCP servers, hooks, commands, agents, and reusable agent packages across Claude Code, Cursor, Google Antigravity, and Codex. They are usually configuring local tools and need to understand what will change before it touches global IDE or agent config.

## Product Purpose

Agent Nexus is a local, review-first control plane for declaring, previewing, syncing, verifying, and tracing agent capabilities from one manifest. Success means a user can trust what is installed, see what is executable, deploy to selected targets, and trace every managed asset back to its package and lockfile.

## Brand Personality

Calm, trustworthy, precise. The product should feel like infrastructure you can rely on: quiet by default, explicit when risk appears, and careful with secrets and local state.

## Anti-references

Do not look like a dense enterprise admin dashboard, a decorative SaaS hero, a generic AI robot tool, or a noisy monitoring wall. Avoid overwhelming metric grids, always-visible secondary detail, glossy gradients, and UI that exposes personal paths or secrets.

## Design Principles

- Progressive disclosure over full exposure: show the next decision first, keep supporting detail nearby but collapsed.
- One primary action per surface: refresh, save, and deploy should never compete visually.
- Safety is visible but quiet: localhost, redaction, and confirmation guarantees should be present without dominating the task.
- Local-first trust: filenames, warnings, and deploy state should make scope clear without leaking private machine details.
- Preserve native workflow semantics: dashboard controls should reflect the same manifest, sync, doctor, and lockfile behavior as the CLI.

## Accessibility & Inclusion

Target WCAG AA contrast, keyboard-accessible controls, semantic headings, clear focus states, readable tabular data, and reduced-motion-safe transitions. Status should not rely on color alone.
