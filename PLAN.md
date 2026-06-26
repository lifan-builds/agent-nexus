# Nexus Active Plan

## Context-Grill Removal (Completed 2026-06-22)

## Goal
Remove `context-grill` from Nexus-managed deployments and keep Matt Pocock's `grilling` as the single active grill-loop skill.

## Changes
- Added an explicit `skills:` allowlist to the `lifan-builds/context-harness` package in `nexus.personal.yml`, excluding only `context-grill`.
- Kept `grilling` and `grill-me` in the `mattpocock/skills` allowlist.
- Updated `AGENTS.md` to document that `context-grill` is intentionally excluded in favor of `grilling`.
- Ran `./nexus.py sync --yes`, which pruned `context-grill` from Claude, Cursor, Antigravity, and Codex.

## Verification
- `./nexus.py sync --dry-run` showed 13 skills and did not include `context-grill`.
- `./nexus.py sync --yes` completed successfully and pruned `context-grill` from all targets.
- `./nexus.py doctor` passed and reports 13 skill symlinks for each configured target.
- `./nexus.py list` shows `grilling` and no `context-grill`.
- `/Users/lfan/.codex/skills/grilling` exists; `/Users/lfan/.codex/skills/context-grill` does not.

## Managed Skill Package Updates (Completed 2026-06-22)

## Goal
Update all Nexus-managed skill packages in `nexus.personal.yml` to their latest remote default-branch revisions and redeploy them.

## Changes
- Confirmed `lifan-builds/context-harness` was already at latest `main`: `b46f83d21cce7c2891c9005fde6e126d0a3e023c`.
- Updated `mattpocock/skills` from `b8be62ffacb0118fa3eaa29a0923c87c8c11985c` to `6eeb81b5fcfeeb5bd531dd47ab2f9f2bbea27461`.
- Updated `Panniantong/Agent-Reach` from `17624268a059ccfb23eba8a2ba50f9f92c8dc0ca` to `22d7f03a59401b5740b380c3ad43e3ff7a9dc373`.
- Updated `pbakaus/impeccable` from `84135db0e6bdd58d22828f7bc8331cae7bde3e7f` to `d2ab4ddee6fa63002fae680652b5fbd31735e280`.
- Removed `zoom-out` from the `mattpocock/skills` allowlist because latest upstream removed that skill.
- Added `domain-modeling`, `codebase-design`, and `grilling` because latest `improve-codebase-architecture` and `grill-me` invoke them.
- Ran `./nexus.py sync --yes`, which deployed 14 managed skills to Claude, Cursor, Antigravity, and Codex.

## Verification
- `git ls-remote --symref` resolved the current remote default-branch commits for all managed skill package repos.
- `./nexus.py sync --dry-run` completed without missing requested skills and showed the 14-skill deployment plan.
- `./nexus.py sync --yes` completed successfully and pruned stale `zoom-out` symlinks from all targets.
- `./nexus.py doctor` passed and reports 14 skill symlinks for each configured target.
- `./nexus.py list` shows the updated package refs and discovered skills: context-harness family, `domain-modeling`, `improve-codebase-architecture`, `codebase-design`, `grill-me`, `grilling`, `agent-reach`, and `impeccable`.

## Grill-Me Skill Re-enable (Completed 2026-06-22)

## Goal
Re-enable the `grill-me` skill through Nexus-managed deployment rather than restoring an unmanaged Codex skill directory.

## Changes
- Added `grill-me` to the `mattpocock/skills` allowlist in `nexus.personal.yml`.
- Ran `./nexus.py sync --yes`, which deployed 12 managed skills to Claude, Cursor, Antigravity, and Codex.
- Regenerated `nexus.personal.lock.yml`; the pinned `mattpocock/skills` package now discovers `improve-codebase-architecture`, `zoom-out`, and `grill-me`.

## Verification
- `./nexus.py sync --dry-run` confirmed `skill: grill-me` would deploy.
- `./nexus.py sync --yes` completed successfully after resolving `lifan-builds/context-harness@main` from cache.
- `./nexus.py doctor` passed and reports 12 skill symlinks for each configured target.
- `/Users/lfan/.codex/skills/grill-me` is a symlink to the pinned `.nexus/cache/github.com/mattpocock/skills/b8be62ffacb0118fa3eaa29a0923c87c8c11985c/skills/productivity/grill-me` directory.

## Codex Skill Audit and Cleanup (Completed 2026-05-26)

## Goal
Inspect Codex-visible skills and compare the Nexus-managed Codex deployment against `nexus.personal.yml` and `nexus.personal.lock.yml`.

## Findings
- `nexus.personal.yml`, `nexus.personal.lock.yml`, `./nexus.py list`, and `./nexus.py doctor` agree on 11 Nexus-managed Codex skills:
  `context-harness`, `context-init`, `context-launch`, `context-catch-up`, `context-maintain`, `context-grill`, `context-handoff`, `improve-codebase-architecture`, `zoom-out`, `agent-reach`, and `impeccable`.
- `/Users/lfan/.codex/skills` has exactly those 11 Nexus-managed symlinks, all pointing into the expected `.nexus/cache/...` package snapshots.
- `/Users/lfan/.codex/skills` also contains unmanaged local skill directories `handoff` and `grill-me`; these are not declared in Nexus and are not counted by `nexus doctor` because they are ordinary directories, not Nexus symlinks.
- Codex also sees `/Users/lfan/.agents/skills/agent-reach`, producing a duplicate `agent-reach` skill source outside Nexus. Its `SKILL.md` hash matches the Nexus-managed `agent-reach`, but the Nexus-managed copy has an extra `SKILL_en.md`.
- System and plugin skills under `/Users/lfan/.codex/skills/.system` and `/Users/lfan/.codex/plugins/cache/...` are Codex/runtime-managed, not Nexus-managed, and should not be treated as manifest drift.

## Verification
- `./nexus.py list` -> reports 11 discovered skills for all targets.
- `./nexus.py doctor` -> passes and reports `codex skills: 11 symlinks`.
- Symlink inspection of `/Users/lfan/.codex/skills` -> all 11 managed links resolve to the current lockfile cache paths.
- Removed unmanaged `/Users/lfan/.codex/skills/handoff`, `/Users/lfan/.codex/skills/grill-me`, and `/Users/lfan/.agents/skills/agent-reach`.
- `./nexus.py sync --yes` -> redeployed the 11 manifest-managed skills to all configured targets.
- Final Codex inventory contains only `.system` plus the 11 Nexus-managed skill symlinks; `/Users/lfan/.agents/skills` has no remaining extra skill entries.

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
