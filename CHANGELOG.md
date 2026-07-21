# Changelog

All notable changes are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- Safe minimal `nexus init` starter and explicit example template.
- Installed-package metadata and project-directory discovery.
- Preview-first clean planning and non-persistent dry-run package inspection.
- Per-MCP target filters with target-aware preview, lockfile ownership, pruning, audit, and doctor checks.
- Dashboard lifecycle guidance, manifest editing, revision checks, accessible confirmation, and responsive tables.
- GitHub community files, CI metadata, quickstart, examples index, and release checklist.

### Changed

- Unknown targets are rejected instead of silently ignored.
- Optional MCP selection is deterministic in dry-run and automation.
- Normal sync no longer removes unrelated repository IDE files.

### Security

- Dashboard deploy is tied to the reviewed plan and manifest revision.
- Clean preserves unmanaged directories, files, hooks, and MCP entries.
