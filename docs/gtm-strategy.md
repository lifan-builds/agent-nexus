# GTM Strategy

Agent Nexus should launch as the safe package manager for serious agent workspaces: one manifest, review before write, native target sync, lockfile traceability, and doctor verification.

## Ideal Customer Profile

Primary users are developers and agent-workspace maintainers who use more than one coding agent and are already juggling MCP servers, skills, hooks, commands, agents, and local config across Claude Code, Cursor, Google Antigravity, and Codex.

They care about:

- avoiding broken global agent config,
- seeing executable MCP and hook changes before writes,
- reusing GitHub or local agent packages,
- keeping local secrets out of shared manifests,
- tracing what was installed after a sync.

## Wedge

Agent Nexus is not a generic dotfiles sync tool and does not need to be the broadest agent hub. The wedge is a reviewable package workflow for agent capabilities:

1. Declare trusted packages, MCPs, hooks, and targets in one manifest.
2. Preview executable changes with dry-run review.
3. Deploy native target files without clobbering unmanaged config.
4. Record package snapshots and generated overlays in a lockfile.
5. Verify the result with `doctor`.

## Messaging Pillars

### Review before write

Lead with `audit` and `sync --dry-run`. The user should understand that Nexus is safe to inspect before it mutates global config.

### Packages, not paste-driven setup

Position GitHub and local packages as reusable units of agent capability: skills, hooks, commands, agents, overlays, and MCP declarations.

### Native target files

Nexus writes each platform's real config format instead of pretending every agent has the same model.

### Traceability after sync

Lockfiles, package snapshots, generated overlays, and doctor checks make the install auditable after the fact.

### Local-first dashboard

The dashboard is a localhost UI for status and policy edits. It redacts MCP env/header values and keeps deploy behind explicit confirmation.

## Launch Assets

Use these assets before broader distribution:

- `README.md` for the primary GitHub pitch and quickstart.
- `docs/assets/dashboard-hero.png` and `docs/assets/dashboard-management.png` for visual proof.
- `docs/demo-transcript.md` for a proof-backed walkthrough.
- `docs/demo-before-after.md` for the pain-to-solution story.
- `docs/security-model.md` for trust objections.
- `docs/comparison.md` for honest category positioning.
- `docs/demo-recording.md` for producing a future terminal GIF or short video.

Do not publish a GIF/video claim until the actual asset is committed and checked for secret/path hygiene.

## Channels

### GitHub

Make the README the source of truth. Pin the repo, use a release note that mirrors the README wedge, and keep issues/discussions open for target requests and package examples.

### Developer communities

Share a short demo and the `audit → dry-run → sync → doctor` flow with Claude Code, Cursor, Codex, Antigravity, and MCP communities. Focus on the config-sprawl problem, not generic AI-tool hype.

### MCP and skill authors

Reach authors who currently document separate install steps per host. Pitch Nexus as a way to ship one package with target overlays and reviewable install behavior.

### Hacker News / Product Hunt

Use these only after proof assets are ready: polished README, sanitized dashboard screenshots, demo transcript, comparison guide, and ideally a short terminal recording.

### Short-form launch post

Lead with a terminal-first story:

> I got tired of hand-editing MCP, skills, and hooks across Claude Code, Cursor, Antigravity, and Codex. Agent Nexus lets you audit first, dry-run every executable change, sync native config, then verify with doctor.

## 30 / 60 / 90 Day Plan

### First 30 days: proof and sharp onboarding

- Polish README, demo transcript, screenshots, and comparison docs.
- Publish one focused launch post with the safe setup path.
- Collect first user objections around install, target support, and package format.
- Add or refine example manifests based on real setup questions.

Success signals:

- GitHub stars and watchers from target users,
- issues/discussions asking for concrete targets or packages,
- external mentions that repeat “review before write” or “safe package manager”.

### Days 31–60: package ecosystem wedge

- Publish 2–3 high-quality example packages or package recipes.
- Recruit MCP/skill authors to test package-based install instructions.
- Improve docs where users hesitate during `audit`, `init`, or `sync --dry-run`.

Success signals:

- package authors linking to Nexus install instructions,
- repeat users adding multiple packages,
- issues shifting from “what is this?” to “support this package/target”.

### Days 61–90: broaden proof carefully

- Produce a sanitized terminal recording if the demo flow is stable.
- Consider Show HN or Product Hunt only with proof assets ready.
- Expand target documentation or support based on actual demand, not broad-coverage claims.

Success signals:

- external comparisons position Nexus around safety and traceability,
- users report successful dry-run-first setup,
- new packages or examples come from outside the original author.

## Metrics

Track what can be measured without adding invasive telemetry:

- GitHub stars, watchers, forks, and clones if available.
- Issues/discussions opened by new users.
- Package or target requests.
- Mentions and backlinks from MCP/skill authors.
- README CTA click proxies where GitHub provides referral signals.
- Demo transcript and docs engagement through external link analytics, if shared from controlled channels.

Avoid optimizing for raw target-count claims. Optimize for trust, repeatable setup, and package adoption.
