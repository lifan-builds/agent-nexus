# Contributing to Agent Nexus

Thanks for improving Agent Nexus. Keep changes review-first, local-first, and non-destructive.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
```

## Before a pull request

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider
python -m py_compile nexus.py
python -m build
python -m twine check dist/*
```

Use temporary `HOME`, `CODEX_HOME`, and workspaces for tests that exercise sync, clean, or the dashboard. Never write to a contributor's real agent configuration.

## Change guidelines

- Preserve unmanaged MCP entries, hooks, files, and local secret values.
- Add a dry-run or preview before new filesystem mutations.
- Update tests and user-facing docs together.
- Keep the dashboard dependency-free and localhost-only.
- Do not include secrets, personal paths, or private package names in fixtures or screenshots.

See [docs/security-model.md](docs/security-model.md) and [docs/release-checklist.md](docs/release-checklist.md).
