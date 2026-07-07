# Demo Recording Instructions

Use this checklist to produce a short terminal recording or GIF without exposing secrets or private local paths.

## Goal

The recording should show the complete trust path in under one minute:

```bash
python nexus.py audit --redact-home
python nexus.py init
$EDITOR nexus.personal.yml
python nexus.py sync --dry-run
python nexus.py sync
python nexus.py doctor
```

If `nexus.personal.yml` already exists, say that `init` refuses to overwrite and show the existing manifest path instead of forcing it.

## Terminal Setup

- Use a clean terminal with a readable monospace font.
- Set the working directory to the Agent Nexus checkout.
- Make the terminal wide enough for dry-run output.
- Use `--redact-home` for audit output.
- Avoid showing real tokens, API keys, private repository names, or private absolute paths.
- Prefer a demo manifest using public packages and placeholder env values.

## Recording Flow

1. Show `python nexus.py audit --redact-home`.
2. Show the manifest snippet, not a full private manifest.
3. Run `python nexus.py sync --dry-run`.
4. Pause on the MCP security review.
5. Pause on the hook review if hooks are present.
6. Pause on `Would deploy` so target coverage is visible.
7. Run `python nexus.py sync` and approve only if using a safe demo environment.
8. Show `nexus.personal.lock.yml` source metadata and managed MCP names.
9. Run `python nexus.py doctor`.

## Suggested Captions

- "Audit first: see existing config before any write."
- "Dry run: review executable MCP and hook commands."
- "Native sync: write each target's own config format."
- "Lockfile: trace package snapshots after sync."
- "Doctor: verify what landed."

## Output Hygiene

Before publishing, verify the recording does not show:

- secret env values,
- auth tokens,
- private usernames in config values,
- private repository URLs,
- unrelated local config content,
- exact home path if you want a generic public asset.

## README GIF Placeholder

Until an actual recording is checked in, README copy should link to `docs/demo-transcript.md` and this checklist rather than pretending a GIF exists.
