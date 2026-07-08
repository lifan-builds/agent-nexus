# Agent Nexus Competitive Improvement Plan

Date: 2026-07-07
Status: active planning document
Audience: future implementation agents working in this repository

## Purpose

This document turns the AGHub/GAAL competitor research into a long-running execution plan for improving Agent Nexus. It is intentionally detailed enough that a future agent can work from it for many sessions without needing to rediscover the strategy.

Agent Nexus should become the safest, most inspectable package workflow for serious multi-agent workspaces:

> Install agent capabilities from GitHub, review every executable change before it touches local config, deploy native target files, and trace the result with a lockfile and doctor.

This is different from trying to be the broadest possible AI-agent hub or a generic dotfiles synchronizer. AGHub currently wins on breadth and hub-style positioning. GAAL currently wins on polished one-YAML machine sync, read-only audit/import, and local-first onboarding. Agent Nexus should close the obvious parity gaps while leaning into its strongest wedge: package composition, safety review, target overlays, lockfile traceability, and doctor verification across Claude Code, Cursor, Google Antigravity, and Codex.

## Strategic Positioning

### Current positioning to use everywhere

Agent Nexus is the safe package manager for your agent workspace.

It installs MCP servers, skills, hooks, and GitHub agent packages across Claude Code, Cursor, Google Antigravity, and Codex from one personal manifest. It previews executable changes before writing, preserves local config, records what landed, and verifies the result.

### Differentiation versus AGHub

AGHub's public strength is broad target coverage and hub-style MCP/skill management. Do not try to out-claim AGHub on supported agent count until Nexus actually supports and tests many more targets.

Use this framing instead:

> AGHub optimizes for breadth. Agent Nexus optimizes for a reviewable package workflow: GitHub package snapshots, target overlays, dry-run security review, lockfile traceability, and doctor verification.

### Differentiation versus GAAL

GAAL's public strength is reproducible machine sync from `gaal.yaml`, polished onboarding, `audit`, `init`, dry-run, local-first trust copy, repo/content sync, and non-destructive MCP upserts.

Use this framing instead:

> GAAL syncs your machine setup. Agent Nexus installs your agent capabilities as packages.

### Claims to avoid

- Do not claim Agent Nexus is the first one-YAML agent manager.
- Do not claim Agent Nexus supports more targets than AGHub or GAAL.
- Do not claim AGHub or GAAL lack a feature unless current docs/source were rechecked in the same work session.
- Do not claim one-click setup until there is an actual one-click installer, GUI, or bootstrap path.
- Do not bury safety review, lockfile, or doctor; these are core differentiators.

## Competitive Research Summary

### AGHub

Publicly verified strengths:

- Claims unified configuration management for 22+/23 AI coding assistants.
- Uses “one hub for every AI coding agent” positioning.
- Names high-visibility targets such as Claude Code, Cursor, OpenAI Codex, Antigravity, OpenCode, Gemini CLI, Windsurf, and GitHub Copilot.
- Strong MCP positioning, including stdio, SSE, and StreamableHTTP transports.
- Advertises portable `.skill` packages with `SKILL.md` metadata.
- Has some source/provenance/hash-style trust story around skill packages, though the research confidence was medium for the full verification story.

Implications for Nexus:

- Nexus needs a public target/resource matrix to counter breadth with clarity.
- Nexus should document MCP transport support explicitly.
- Nexus should show why package snapshots + lockfiles are stronger for serious workflows than generic hub breadth.
- Nexus should avoid vague “every agent platform” language and instead name tested targets.

### GAAL

Publicly verified strengths:

- Strong hero: “One YAML. Every coding agent. Every machine.”
- Clear `gaal.yaml` manifest story for dotfiles/reproducible setup.
- Claimed broad auto-detected target coverage; sources varied between 17 and 20 agents.
- Manages repositories, skills, MCP servers, content files/directories, AGENTS.md, rules, commands, hooks, settings, and local sync hooks.
- Polished onboarding around `gaal audit`, `gaal init`, `gaal sync --dry-run`, `gaal sync`, and doctor/status checks.
- `audit` is read-only and scans project, home, package-manager/extension locations, and MCP configs before changes.
- Strong trust copy: local-first, no account, no server, no telemetry by default.
- Non-destructive MCP upserts preserving unrelated/user-managed settings.
- Safer repo handling claims: refuse non-empty clone destinations, URL mismatch checks, archive safety guards.

Implications for Nexus:

- `nexus audit` is the biggest missing parity feature.
- Docs need to feel as intentional as GAAL's five-minute quickstart.
- Local-first/no-telemetry trust should be explicitly stated if true.
- Nexus should not chase generic repo/content sync until package workflow is clearly superior.

## Current Agent Nexus Strengths

Based on current repo and known capabilities, Agent Nexus already has several ingredients that can be stronger than AGHub/GAAL if documented and hardened:

- `nexus.yml` / `nexus.personal.yml` manifest model.
- GitHub and local-path packages.
- Auto-discovery of skills, hooks, commands, and agents.
- MCP declarations and optional MCPs.
- Target overlays for per-platform skill metadata.
- `sync --dry-run` review.
- MCP security review before executable config write.
- Non-destructive MCP merge preserving unmanaged servers and env placeholders.
- Codex managed TOML block isolation.
- Hook dedupe and stale managed hook cleanup.
- Lockfile traceability.
- `doctor` diagnostics.
- Four core native targets: Claude Code, Cursor, Google Antigravity, and Codex, plus 41 skills target presets behind explicit `targets: ["*"]` opt-in.
- Python single-file implementation with PyYAML as the only runtime dependency.

## North Star User Experience

A skeptical power user should be able to do this in five minutes:

```bash
python nexus.py audit
python nexus.py init
$EDITOR nexus.personal.yml
python nexus.py sync --dry-run
python nexus.py sync
python nexus.py doctor
```

The output should answer:

1. Which agent targets were detected?
2. Which MCP servers, skills, hooks, commands, and agents already exist?
3. What will Nexus manage?
4. Which executable MCP commands will be registered?
5. What unmanaged config will be preserved?
6. Which package commits are being installed?
7. Which target files changed?
8. How can the user verify or roll back?

## Phase 0: Baseline And Guardrails

Goal: make sure future agents understand the current state before changing behavior.

### Tasks

- [x] Read `NOW.md`, `CONTEXT.md`, `PLAN.md`, `README.md`, `docs/security-model.md`, `docs/demo-transcript.md`, `nexus.example.yml`, `nexus.py`, and `tests/test_nexus.py` before implementation.
- [x] Run current verification commands and record results in `PLAN.md`:
  - `python -m pytest tests`
  - `python -m py_compile nexus.py`
  - `python nexus.py sync --dry-run`
  - `python nexus.py doctor`
- [x] Capture current CLI help output for all commands.
- [x] Identify any mismatch between README claims and actual code behavior.
- [x] Identify files that are local-only or gitignored and must not be changed for public docs.

### Acceptance criteria

- Future work starts from verified current behavior, not assumptions.
- Any README/docs claim that is not implemented is either removed, marked planned, or backed by an issue/plan entry.
- `PLAN.md` and `NOW.md` reflect the current implementation state.

## Phase 1: Public Positioning And Docs Parity

Goal: make Agent Nexus as easy to understand as AGHub and GAAL.

### 1.1 README restructure

Update README so the top half contains:

1. Hero: “The safe package manager for your agent workspace.”
2. One-sentence pitch.
3. 60-second demo GIF placeholder or actual asset.
4. Minimal YAML example.
5. Dry-run review output.
6. Supported target/resource matrix.
7. Safety model summary.
8. Quickstart.
9. Links to deeper docs.

Do not bury safety and verification at the bottom.

### 1.2 Target/resource matrix

Create `docs/targets.md` with a matrix like:

| Resource | Claude Code | Cursor | Antigravity | Codex | Status |
| --- | --- | --- | --- | --- | --- |
| Skills | deployed | deployed | deployed | deployed | implemented |
| MCP stdio | merged | merged | merged | managed block | implemented |
| MCP SSE | TBD | TBD | TBD | TBD | verify/implement |
| MCP StreamableHTTP | TBD | TBD | TBD | TBD | verify/implement |
| Hooks | repo hook copy | repo hook merge | not deployed | managed hook merge | partial |
| Commands | discovered | discovered | discovered | discovered | lockfile only |
| Agents | discovered | discovered | discovered | discovered | lockfile only |
| Target overlays | generated | generated | generated | generated | implemented |
| Lockfile | records | records | records | records | implemented |

Each row must separate implemented, discovered-only, and planned behavior.

### 1.3 Manifest docs

Create `docs/manifest.md` documenting:

- manifest precedence: `nexus.personal.yml`, then `nexus.yml`
- `name`
- `version`
- `targets`
- `packages`
- `repo`
- `path`
- `ref`
- `targets` per package
- `skills` filter
- `hooks` filter / disable behavior
- `sparse_paths`
- `skill_overrides`
- `mcps`
- `optional_mcps`
- env placeholder behavior
- examples for individual use, team use, mcp-only use, and package-only use

### 1.4 Package docs

Create `docs/packages.md` documenting:

- what a Nexus package is
- supported package sources
- asset discovery rules
- `SKILL.md` discovery
- hook file discovery
- `commands/*.md` discovery
- `agents/*.md` discovery
- overlay generation
- cache layout under `.nexus/cache/`
- how refs resolve to commit SHA snapshots
- how lockfile records package metadata
- what package contents are executable versus inert
- how to inspect a package before syncing

### 1.5 Comparison docs

Create `docs/comparison.md` with honest, non-hostile framing:

- Agent Nexus vs AGHub
- Agent Nexus vs GAAL
- Agent Nexus vs native plugin systems

Use “choose based on workflow” language.

Required framing:

- AGHub: broad hub and high target count.
- GAAL: reproducible machine/dotfiles sync and polished audit onboarding.
- Agent Nexus: safe package workflow with GitHub package snapshots, overlays, dry-run review, lockfile, and doctor.

Do not include unsupported claims that competitors lack specific features.

### Acceptance criteria

- README claims match code.
- Docs clearly distinguish implemented, partial, and planned behavior.
- A new user can understand why Nexus exists even after seeing AGHub and GAAL.
- No stale competitor claims remain.

## Phase 2: `nexus audit` Read-only Discovery

Goal: close the biggest GAAL parity gap.

### Why this matters

GAAL’s `audit` reduces fear by showing current state before any write. Agent Nexus writes global IDE config, so it needs the same trust-building step.

### Command design

Add:

```bash
python nexus.py audit
python nexus.py audit --json
python nexus.py audit --target claude
python nexus.py audit --target cursor
python nexus.py audit --target antigravity
python nexus.py audit --target codex
```

### Audit should detect

For each target:

- target root directory exists / missing
- skill directory exists / missing
- MCP config file exists / missing
- hooks file exists / missing where applicable
- existing MCP server names
- existing MCP transport type where inferable
- existing commands/args for stdio MCPs
- env keys present, but never print secret values
- Nexus-managed MCP entries from prior lockfile or managed markers
- unmanaged MCP entries
- Nexus-managed hooks
- unmanaged hooks
- skill symlinks pointing into `.nexus/cache/` or `.nexus/generated/`
- stale symlinks pointing nowhere
- previous lockfile presence

### Suggested human output

```text
==> nexus audit

Targets:
  + claude: ~/.claude detected
  + cursor: ~/.cursor detected
  - antigravity: config not found
  + codex: ~/.codex detected

MCP servers:
  claude:
    unmanaged: github, playwright
    nexus-managed: context7
  cursor:
    unmanaged: github
  codex:
    none

Skills:
  claude: 6 Nexus symlinks, 2 unmanaged dirs
  cursor: 6 Nexus symlinks
  antigravity: not found
  codex: 5 Nexus symlinks, 1 stale symlink

Suggested manifest snippets:
  mcps:
    - name: github
      command: npx
      args: ["-y", "@modelcontextprotocol/server-github"]
      env:
        GITHUB_TOKEN: "${GITHUB_TOKEN}"
```

### JSON output

`audit --json` should be machine-readable and safe for logs:

- no env values
- no auth tokens
- no personal secrets
- paths are okay unless there is a privacy concern; if uncertain, support `--redact-home`

### Implementation notes

- Reuse existing target path constants and config parsers where possible.
- Do not mutate any files.
- Do not fetch packages.
- Do not write lockfiles.
- Do not create missing directories.
- Tests should use temporary HOME/CODEX_HOME fixtures.

### Tests

Add tests for:

- [x] empty machine audit
- [x] Claude MCP audit with env values redacted
- [x] Cursor MCP audit with unmanaged entries
- [x] Codex TOML managed block audit
- [x] stale skill symlink detection
- [x] unmanaged skill directory detection
- [x] hook audit with Nexus-managed and unmanaged hooks
- [x] `--json` output redacts env values

### Acceptance criteria

- [x] `nexus audit` exits 0 on a machine with no agent configs.
- [x] `nexus audit` exits 0 on fixture configs with mixed managed/unmanaged resources.
- [x] Output never prints secret values.
- [x] The README quickstart can recommend audit before init/sync.

## Phase 3: MCP Transport And Merge Semantics

Goal: match AGHub’s explicit MCP transport story and beat competitors on safety docs/tests.

### Tasks

- [x] Inventory current MCP schema support in `nexus.py`.
- [x] Document which transports are supported now:
  - stdio command/args
  - SSE URL
  - StreamableHTTP URL
  - any target-specific limitations
- [x] If SSE/StreamableHTTP are not supported, implement only if the target config formats are clear and tests can prove behavior.
- [x] Add `docs/mcp.md` covering:
  - schema examples
  - per-target output formats
  - env placeholder behavior
  - non-destructive merge semantics
  - managed vs unmanaged entries
  - Codex managed TOML block behavior
  - stale managed MCP pruning
- [x] Add golden-file tests for each target.

### Golden test cases

Required fixtures:

1. [x] Add new stdio MCP to empty target config.
2. [x] Update existing managed stdio MCP command/args.
3. [x] Preserve unmanaged MCP server.
4. [x] Preserve local env value when manifest says `${TOKEN}`.
5. [x] Preserve local-only env keys not mentioned by manifest.
6. [x] Preserve local-only server keys not mentioned by manifest.
7. [x] Remove stale Nexus-managed MCP from previous lockfile.
8. [x] Do not remove skipped optional MCP that was never accepted.
9. [x] Codex TOML preserves content outside managed block.
10. [x] JSON target preserves formatting reasonably or documents formatting behavior.

### Acceptance criteria

- A skeptical user can read docs and tests to understand exactly what will happen to existing MCP config.
- AGHub’s transport support is no longer a messaging advantage without an answer.
- Safety claims are backed by tests.

## Phase 4: Package Trust And Lockfile Leadership

Goal: make package safety and traceability the clearest Agent Nexus advantage.

### Package trust policy

Create `docs/package-trust.md` explaining:

- [x] package sources supported today
- [x] what `ref` means
- [x] why pinning to tags/SHAs is safer than `main`
- [x] how Nexus resolves GitHub refs
- [x] where package snapshots are cached
- [x] whether package install runs code during discovery
- [x] which package assets can become executable after sync:
  - MCP commands
  - hooks
  - possibly scripts referenced by hooks
- [x] how dry-run exposes executable changes
- [x] how lockfile lets users trace installed assets
- [x] how to review a package manually before sync

### CLI improvements

Implement or plan:

```bash
python nexus.py package inspect <package-name-or-repo>
python nexus.py package list
python nexus.py lock show
python nexus.py lock diff
```

If these are too large for the first implementation pass, start with docs plus tests around existing lockfile contents.

### Lockfile improvements

Ensure lockfile records:

- [x] Nexus version
- [x] generation time
- [x] manifest file used
- [x] package repo/path
- [x] requested ref
- [x] resolved commit SHA
- [x] cache path
- [x] discovered assets
- [x] selected targets
- [x] generated overlays
- [x] managed MCP names
- [x] hook deployment targets
- [x] optional MCPs accepted for this sync

Consider adding:

- [ ] package content hash summary
- [x] source URL
- [x] warnings for floating refs such as `main`
- [ ] previous lockfile comparison summary

### Tests

- package from GitHub fixture or local fixture records expected lockfile metadata
- package with selected skills only records selected deployment
- package with overlays records generated overlay paths
- optional MCP acceptance/rejection lockfile semantics
- floating ref warning, if implemented

### Acceptance criteria

- Launch copy can honestly say: “Review before write. Trace after sync.”
- Lockfile becomes a visible differentiator versus GAAL if GAAL lockfile semantics remain unclear.
- Package trust story is concrete enough for security-sensitive users.

## Phase 5: Hook Lifecycle Hardening

Goal: make hooks a safe differentiator, not a hidden risk.

### Tasks

- [x] Document hook discovery paths and target behavior.
- [x] Document which hooks are executable and when they run.
- [x] Show hook changes in dry-run output.
- [x] Add hook security review output if not already present.
- [x] Preserve unmanaged hooks for all targets.
- [x] Deduplicate managed hooks by normalized content.
- [x] Remove stale Nexus-managed hooks only when they are marked as Nexus-managed.
- [x] Add tests for Cursor and Codex hook merging.
- [x] Clarify Claude/Antigravity hook support or non-support in matrix.

### Acceptance criteria

- [x] Users can tell exactly which hook commands Nexus will install.
- [x] A stale hook from a removed package is pruned safely.
- [x] An unmanaged user hook is never deleted.
- [x] Dry-run and docs make hook execution risk visible.

## Phase 6: Examples And Demo Assets

Goal: give Agent Nexus the public proof that AGHub and GAAL already have through polished pages/docs.

### Example manifests

Add an `examples/` directory:

- [x] `examples/minimal.yml`
  - Claude + Cursor
  - one package
  - one MCP
- [x] `examples/context-harness.yml`
  - all four targets
  - Context Harness package
  - common MCP servers
  - Codex hooks
- [x] `examples/mcp-only.yml`
  - no packages
  - just MCP fan-out
- [x] `examples/team.yml`
  - env placeholders
  - comments about committing shared config
- [x] `examples/package-overlays.yml`
  - target overlays example

### Demo assets

Create or update:

- [x] `docs/demo-transcript.md`
- [x] `docs/demo-before-after.md`
- [x] terminal recording instructions
- [x] screenshot checklist
- [x] README GIF placeholder

### Required demo flow

The flagship demo should show:

1. [x] `nexus audit`
2. [x] `nexus init`
3. [x] edit `nexus.personal.yml`
4. [x] `nexus sync --dry-run`
5. [x] MCP security review
6. [x] target deploy plan
7. [x] `nexus sync`
8. [x] lockfile generated
9. [x] `nexus doctor`
10. [x] per-target proof that skill/MCP landed

### Acceptance criteria

- [x] A visitor can understand the product from one GIF and one YAML snippet.
- [x] A user can copy an example manifest and adapt it.
- [x] The demo does not require secrets or private local paths.

## Phase 7: Install And Distribution Polish

Goal: reduce onboarding friction without overcommitting to a rewrite.

Status: complete for the clone-based release path. README now has one recommended clone + `scripts/install-local.sh` path, and the installer is reversible and refuses to overwrite unrelated `nexus` commands unless forced.

### Near-term options

- [x] Keep clone-based install but make it feel official:

```bash
git clone https://github.com/lifan-builds/agent-nexus.git ~/.agent-nexus
cd ~/.agent-nexus
python -m pip install pyyaml
python nexus.py init
```

- [x] Add a `nexus` wrapper script installation step:

```bash
ln -sf "$PWD/nexus.py" ~/.local/bin/nexus
```

- [x] Add `scripts/install-local.sh` if safe and reversible.

### Medium-term options

- `pipx install agent-nexus`
- `uv tool install agent-nexus`
- Homebrew tap
- GitHub releases with a packaged Python zipapp

### Non-goals for now

- Do not rewrite in Go solely for distribution unless Python packaging becomes a real blocker.
- Do not add a GUI before the terminal path is polished.

### Acceptance criteria

- Quickstart has one recommended install path.
- The install path is reversible.
- The README no longer feels like “clone this repo and figure it out.”

## Phase 8: Target Expansion Strategy

Goal: decide how to respond to AGHub/GAAL target-count advantage.

### Principle

Target count is useful only if each adapter is real, tested, and documented. Do not chase vanity support.

### Candidate targets

Consider after P0/P1 work is complete:

1. Windsurf
2. Gemini CLI
3. GitHub Copilot / VS Code
4. OpenCode
5. Claude Desktop MCP-only mode

### Target-adapter acceptance criteria

For each new target:

- documented skill path or explicit “skills unsupported” note
- documented MCP config path and format
- merge tests
- dry-run output
- doctor checks
- example config fixture
- target matrix row updated
- demo proof if target is included in marketing copy

### Messaging

Until target expansion is real, use:

> Built for Claude Code, Cursor, Google Antigravity, and Codex.

Do not use:

> Every agent platform.

## Phase 9: CI, Test Harness, And Release Quality

Goal: make safety claims continuously verifiable.

### Tasks

- [ ] Add or update CI to run tests on macOS/Linux if feasible.
- [ ] Ensure tests do not touch real HOME or real agent configs.
- [ ] Use temporary HOME/CODEX_HOME in all filesystem tests.
- [ ] Add golden fixture snapshots for target config writes.
- [x] Add CLI smoke tests for `init`, `audit`, `sync --dry-run`, `doctor`, and error cases.
- [x] Add py_compile check.
- [ ] Add README/docs link checker if lightweight.

### Acceptance criteria

- No test mutates user-global agent config.
- CI proves the core safety invariants.
- Release checklist has exact commands and expected outcomes.

## Phase 10: Launch-Ready Story

Goal: prepare public release assets once product/docs parity is real.

### Required launch assets

- README with demo GIF.
- `docs/quickstart.md` or README quickstart polished enough to stand alone.
- `docs/targets.md` target/resource matrix.
- `docs/security-model.md` linked above fold.
- `docs/comparison.md` comparing AGHub/GAAL honestly.
- `examples/` directory.
- `docs/demo-transcript.md` current with actual output.
- `CHANGELOG.md` or release notes if a release tag is created.

### Launch headline options

- “Agent Nexus: a safe package manager for Claude Code, Cursor, Antigravity, and Codex workspaces.”
- “Install MCPs, skills, hooks, and agent packages from one personal manifest.”
- “Review before write. Trace after sync.”

### Launch body skeleton

```text
I kept rebuilding the same agent setup across Claude Code, Cursor, Antigravity, and Codex: MCP servers in different config formats, skills in different folders, hooks in different places, and no reliable way to prove what changed.

Agent Nexus is my attempt to make that setup safe and portable.

You define one personal manifest with packages, MCP servers, skills, hooks, and targets. `sync --dry-run` shows the executable MCP commands and deploy plan, `sync` writes native config, and `doctor` verifies what landed. The lockfile records which package snapshot installed which assets.

It is not trying to be the broadest hub. It is for people who want an inspectable package workflow for the coding agents they actually use.
```

### Channels

Prioritize targeted replies and niche forums before broad launches:

- developers complaining about MCP config drift
- Claude Code + Cursor users
- Codex/Antigravity early adopters
- MCP server authors who need install instructions for multiple hosts
- agent-skill/package directory maintainers
- GitHub issues/discussions asking for multi-client setup

Only use Show HN/Product Hunt after proof assets are ready.

## Implementation Order For Future Agents

If a future agent has no other instruction, work in this order:

1. Read current context and verify current tests.
2. Update README/docs to match current positioning and actual behavior.
3. Add `docs/targets.md` and `docs/manifest.md`.
4. Add `examples/` manifests.
5. Add `nexus audit` with tests.
6. Add `docs/packages.md` and package trust docs.
7. Harden MCP merge tests and document transports.
8. Harden hook lifecycle tests and dry-run output.
9. Add demo transcript/assets.
10. Improve install path.
11. Add honest comparison docs.
12. Only then consider target expansion.

## Work Session Template

At the start of each session:

1. Read `NOW.md`.
2. Read this file.
3. Read relevant sections of `CONTEXT.md`.
4. Run the smallest verification command that establishes baseline state.
5. Pick the next unchecked task in order unless the user directs otherwise.

Before editing:

- Check `git status --short`.
- Do not overwrite personal manifests or lockfiles unless the task explicitly requires it.
- Prefer tests with temporary HOME/CODEX_HOME.
- Keep README claims aligned with implemented behavior.

Before ending:

- Run relevant tests.
- Update `PLAN.md` with task-local progress.
- Update `NOW.md` with current focus, blockers, next step, and touched files.
- If `CONTEXT.md` changed, run `node scripts/context-index.js update`.

## Verification Commands

Use these as applicable:

```bash
python -m pytest tests
python -m py_compile nexus.py
python nexus.py sync --dry-run
python nexus.py doctor
```

For docs-only changes:

```bash
python - <<'PY'
from pathlib import Path
fence = chr(96) * 3
for path in ['README.md', 'COMPETITIVE_IMPROVEMENT_PLAN.md']:
    text = Path(path).read_text()
    assert text.count(fence) % 2 == 0, path
print('markdown fences balanced')
PY
```

## Definition Of Done For This Roadmap

Agent Nexus is competitively ready when:

- A new user can understand the product in under one minute.
- A skeptical user can run audit/dry-run before any writes.
- Docs show exactly which targets/resources are implemented.
- Safety behavior is backed by tests and documented examples.
- Package trust and lockfile traceability are clear.
- Demo assets prove the full workflow.
- Comparison docs honestly explain when to choose Agent Nexus, AGHub, GAAL, or native tools.
- Launch copy no longer depends on vague “one YAML” or unsupported competitor claims.
