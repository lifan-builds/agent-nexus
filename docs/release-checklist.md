# Release checklist

- [ ] Confirm the working tree contains no secrets or personal paths.
- [ ] Verify current target paths against official tool behavior.
- [ ] Run `python -m py_compile nexus.py`.
- [ ] Run the full pytest suite without cache or bytecode output.
- [ ] Verify dry-run leaves workspace, `HOME`, and `CODEX_HOME` unchanged.
- [ ] Verify clean preserves unmanaged `.github`, `.cursor`, `.claude`, hooks, and MCP entries.
- [ ] Build wheel and sdist; run `twine check`.
- [ ] Install the wheel in a clean environment and run version, audit, init, dry-run, doctor, and dashboard JSON smoke tests.
- [ ] Run dashboard browser tests at desktop and mobile widths.
- [ ] Run Lighthouse accessibility checks and keyboard/zoom/reduced-motion review.
- [ ] Validate relative Markdown links and example YAML.
- [ ] Refresh screenshots from sanitized fixture data only.
- [ ] Update `CHANGELOG.md` and version metadata.
