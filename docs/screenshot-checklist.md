# Screenshot Checklist

Use these screenshots to support launch pages, README assets, or issue replies.

## Required Screenshots

- `nexus audit --redact-home` showing detected targets and managed/unmanaged resources.
- `nexus sync --dry-run` showing MCP security review.
- `nexus sync --dry-run` showing hook command review when hooks are configured.
- `nexus sync --dry-run` showing the target deploy plan.
- A redacted manifest snippet with targets, one package, and one MCP.
- A lockfile excerpt showing package source metadata, discovered assets, target deployments, overlays, and managed MCP names.
- `nexus doctor` showing healthy target checks.
- `docs/assets/dashboard-hero.png` showing the refreshed localhost dashboard overview.
- `docs/assets/dashboard-management.png` showing target policy or platform health with confirmed deploy controls.

## README Diagram Assets

- `docs/assets/trust-path.svg` is a static diagram for the review-first workflow; keep it accessible with `<title>` and `<desc>`.
- Do not reference a demo GIF in the README unless the GIF is actually committed.

## Redaction Rules

Do not show:

- real secret values,
- real API tokens,
- private repository names unless intentionally public,
- unrelated personal MCP servers,
- unrelated local hook commands,
- absolute home paths in public docs unless they are generic examples.

Use:

- `${TOKEN}` placeholders,
- `~` home paths,
- public package examples,
- cropped output focused on Nexus-managed rows.

## Visual Quality

- Use a terminal width that avoids wrapping core command lines.
- Keep screenshots short enough that the headline behavior is visible without zooming.
- Prefer light or dark mode consistently across the asset set.
- Include the command prompt line so viewers know what produced the output.
- Use captions that name the safety property being shown.

## Captions

- "Read-only audit before writing config."
- "Executable MCP and hook review during dry run."
- "Native target deployment from one manifest."
- "Lockfile traceability after sync."
- "Doctor verifies target state."
