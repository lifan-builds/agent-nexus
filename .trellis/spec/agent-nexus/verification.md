# Verification

## Native checks

Run from the repository root as applicable:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider tests/test_dashboard_browser.py
python3 -m py_compile nexus.py
node --check scripts/context-index.js
node --check scripts/context-gen.js
node --check scripts/lib.js
```

Run packaging in a detached disposable worktree because build output overlaps tracked generated paths:

```bash
python3 -m build
python3 -m twine check dist/*
```

The repository has no configured lint or static typecheck command. Do not report `ruff`, Mypy, Pyright, or another invented check as required. Browser checks that cannot run because the browser/runtime is unavailable must be reported as skipped or failed with the reason.

## Isolation

Tests and smoke checks that exercise deployment use temporary `HOME`, `CODEX_HOME`, and workspace paths. Do not run `nexus sync`, `nexus doctor`, or cleanup against ignored personal/global state unless that deployment is explicitly the task and has a reviewed preview.

Trellis lifecycle validation must use a detached disposable worktree because task archive/journal behavior may commit automatically. Never use the existing `00-bootstrap-guidelines` task as a fixture.

## Structural checks

- Parse changed JSON, YAML, and TOML with their native parsers.
- Verify registered Claude and Codex hook command targets exist; distinguish project-local hook registration from user-global activation.
- Run Trellis full/phase/package context and task-state commands.
- Run `git diff --check` and review every changed/staged path for scope and sensitivity.
- Search remaining Context Harness terms and classify them as product, example, history, compatibility, or defect.

Evidence anchors: `CONTRIBUTING.md`, `pyproject.toml`, `.github/workflows/ci.yml` where present, and `tests/`.
