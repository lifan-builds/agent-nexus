# Nexus Active Plan

## Impeccable Skill Deployment (Completed 2026-05-23)

## Goal
Add the Impeccable UI design agent skill to the personal Nexus manifest and deploy it to configured IDE targets.

## Progress
- [x] Added `pbakaus/impeccable` to `nexus.personal.yml` using sparse path `.agents/skills/impeccable`.
- [x] Updated Nexus discovery so explicitly requested hidden sparse roots are scanned without broadly traversing hidden directories.
- [x] Added a regression test for hidden sparse skill discovery.
- [x] Ran dry-run sync security review, then deployed with `./nexus.py sync --yes`.

## Verification
- `pytest -q tests/test_nexus.py` -> 17 passed.
- `python3 -m py_compile nexus.py` -> passed.
- `./nexus.py sync --dry-run` -> confirmed `skill: impeccable` would deploy.
- `./nexus.py sync --yes` -> deployed 12 skills including `impeccable` to Claude, Cursor, Antigravity, and Codex.
- `./nexus.py doctor` -> passed; all four targets report 12 skill symlinks.

## Codex Hook Deployment (Completed 2026-05-22)

## Goal
Make hook assets first-class package assets across targets, including Codex lifecycle hooks from context-harness.

## Progress
- [x] Discover `hooks/hooks-codex.json` and root `hooks-codex.json`.
- [x] Support package-level `hooks:` filtering with omitted = auto-discover, `false`/`[]` = no hooks, and lists such as `["codex"]`.
- [x] Deploy Codex hooks to `CODEX_HOME/hooks.json` when set, otherwise `~/.codex/hooks.json`.
- [x] Preserve unmanaged Codex hooks, strip stale Nexus-managed commands marked with `--nexus-package`, substitute `{{package_root}}`, and deduplicate repeated entries.
- [x] Include Codex hooks in dry-run, lock metadata, list output, doctor output, and `nexus.example.yml`.
- [x] Add tests for discovery, filtering, substitution, merge/preserve/stale cleanup, dedupe, and dry-run no-write behavior.

## Verification
- `pytest -q` -> 15 passed.
- `python -m py_compile nexus.py` -> passed.
- `./nexus.py sync --dry-run --all` -> showed `context-harness -> codex`.
- `./nexus.py sync --yes --all` -> deployed 3 Codex hook entries to `/Users/lfan/.codex/hooks.json`.
- `./nexus.py doctor` -> Codex hooks: 3 entries.

## Decisions
- Codex hook deployment treats commands containing `--nexus-package` as Nexus-managed for cleanup; unmanaged user hooks are left intact.
- Codex hook tests use a temp `CODEX_HOME`/fake config and never read the real local `~/.codex/hooks.json`.

## Nexus Go Rewrite (v1.0)

## Goal
Ship `nexus` as a single static Go binary with all 4 subcommands, shell completions, and cross-platform releases — replacing the Python prototype and surpassing Kasetto.

## Progress
- [ ] `go mod init` + project scaffold (cobra CLI, gopkg.in/yaml.v3)
- [ ] Port `nexus sync` — fetch packages (go-git or shell git), auto-discover assets, compile skills, merge MCPs, dedup hooks, security review gate
- [ ] Port `nexus list` — show installed packages, skills, MCPs
- [ ] Port `nexus doctor` — health checks (symlinks, MCP configs, hook dedup, lockfile consistency)
- [ ] Port `nexus clean` — remove all tracked artifacts using lockfile
- [ ] Add `nexus init` — generate nexus.yml from scratch or migrate from apm.yml
- [ ] Add `nexus add <repo>` — add a package interactively
- [ ] Add `nexus update [package]` — bump to latest ref
- [ ] Shell completions (cobra auto-generates bash, zsh, fish, powershell)
- [ ] Cross-compile for macOS arm64/amd64, Linux amd64
- [ ] GitHub releases + `brew install`

## Findings
See archived FINDINGS.md for ecosystem research (Kasetto, APM, Skills CLI). Key points:
- Kasetto gaps we cover: hooks management, hybrid packages, inline MCPs, security gate, optional deps
- APM bugs we fix: hook duplication (84→1), hybrid misclassification, no MCP deployment
- Go chosen over Rust: no borrow checker, go-git for native git, built-in YAML/JSON, easy cross-compile

## Decisions
- **Shell prototype as spec**: `nexus.sh` / `nexus.py` stay as the working spec until Go binary is validated end-to-end.
- **go-git vs shell git**: Prefer shelling out to `git` for simplicity unless native git ops prove necessary.
- **Single binary, no runtime deps**: Matches nexus.py's zero-dep philosophy.

## Archive
### Phase 0–2 (Complete as of 2026-04-12)
Bootstrap (APM setup, context-harness, symlinks), Nexus design (manifest schema, ecosystem research, Kasetto gap analysis), and CLI implementation (nexus.sh/nexus.py with sync/list/doctor/clean). Results: 15 skills deployed (vs 1 with APM), hooks deduplicated 84→1, MCPs synced to 3 IDEs, lockfile generated. deploy.sh removed.
