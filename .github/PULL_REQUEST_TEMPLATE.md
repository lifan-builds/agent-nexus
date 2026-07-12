## Summary

## User journey changed

## Safety and ownership review

- [ ] Dry-run/preview behavior is covered
- [ ] Unmanaged config and secrets are preserved
- [ ] Tests use temporary homes/workspaces
- [ ] Documentation matches behavior

## Verification

- [ ] `python -m pytest -q -p no:cacheprovider`
- [ ] `python -m py_compile nexus.py`
- [ ] Relevant CLI/dashboard flow exercised end to end
