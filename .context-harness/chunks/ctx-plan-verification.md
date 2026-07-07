# Verification

- `python -m pytest tests/test_nexus.py -k install_local` exits 0 with 4 passed after install polish.
- `python -m pytest tests` exits 0 with 57 passed after install polish.
- `python -m py_compile nexus.py` exits 0 after install polish.
- Markdown fence validation exits 0 after install polish.
- `python -m pytest tests` exits 0 with 53 passed after adding demo proof assets.
- `python -m py_compile nexus.py` exits 0 after adding demo proof assets.
- Markdown fence validation exits 0 after adding demo proof assets.
- Example manifest YAML validation exits 0 after adding demo proof assets.
- `python -m pytest tests` exits 0 with 53 passed after hook lifecycle hardening.
- `python -m py_compile nexus.py` exits 0 after hook lifecycle hardening.
- `python nexus.py sync --dry-run` exits 0 and now prints hook command review output before deployment plan.
- Markdown fence validation exits 0 after hook docs updates.
- `python -m pytest tests` exits 0 with 52 passed after adding MCP golden-style coverage.
- `python -m py_compile nexus.py` exits 0 after adding MCP golden-style coverage.
- Markdown fence validation exits 0 after marking MCP roadmap coverage complete.
- `python -m pytest tests` exits 0 with 48 passed after enriching lockfile metadata.
- `python -m py_compile nexus.py` exits 0 after enriching lockfile metadata.
- Markdown fence validation exits 0 after lockfile docs updates.
- `python -m pytest tests` exits 0 with 47 passed after implementing `nexus audit`.
- `python -m py_compile nexus.py` exits 0 after implementing `nexus audit`.
- `python nexus.py audit --json --redact-home` exits 0 and prints redacted machine-readable inventory.
- `python nexus.py audit --target codex --redact-home` exits 0 and prints human-readable target inventory.
- Markdown fence validation exits 0 after audit docs updates.
- `python -m pytest tests` exits 0 with 41 passed after adding package trust/MCP docs.
- `python -m py_compile nexus.py` exits 0 after adding package trust/MCP docs.
- Markdown fence validation exits 0 for README, competitive roadmap, and all top-level docs files.
- `python -m pytest tests` exits 0 with 41 passed after adding docs/examples.
- `python -m py_compile nexus.py` exits 0 after adding docs/examples.
- Markdown fence validation exits 0 for README, competitive roadmap, and docs files.
- Example manifest YAML validation exits 0 for all files under `examples/*.yml`.
- Baseline `python nexus.py sync --dry-run` exits 0 and shows current package/MCP deploy plan without writing target configs.
- Baseline `python nexus.py doctor` exits 0 against the current local deployment.
- Captured CLI help for top-level, `sync`, `list`, `doctor`, `dashboard`, `clean`, `init`, and `version`.
- `python3 -m pytest -q -p no:cacheprovider tests/test_nexus.py` exits 0 with
  33 passed.
- `python3 -c "import py_compile; py_compile.compile('nexus.py', cfile='/tmp/agent-nexus-nexus.pyc', doraise=True)"`
  exits 0.
- `python3 nexus.py doctor` exits 0 against the current local deployment.
- `python3 nexus.py sync --dry-run` against the local Context Harness release
  candidate exits 0, writes no target config or lockfile, and discovers 6 Context
  Harness skills including `set-goal`.
- `python3 nexus.py sync --yes` exits 0 against the local Context Harness
  release candidate, prunes removed `context-launch`/`context-handoff`
  symlinks, deploys `set-goal`, syncs MCPs, and writes
  `nexus.personal.lock.yml`.
- After Context Harness was pushed, `python3 nexus.py sync --yes` fetched
  `lifan-builds/context-harness@main` from GitHub and deployed it locally.
- Post-sync `python3 nexus.py doctor` exits 0 with 13 Claude/Cursor/Antigravity
  skill symlinks, 12 Codex skill symlinks, 4 MCP servers on each configured
  target, and 3 Codex hook entries.
- `node scripts/context-index.js check` exits 0 after this compacted plan.
