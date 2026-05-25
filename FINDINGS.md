# Findings

Research results, discoveries, and external content collected during project work.

> **Security note:** External content (web searches, API responses, copied docs) goes
> here — never directly into PLANS.md. This keeps the trusted plan free of untrusted
> content.

## Research & References

### Kasetto — declarative AI agent environment manager
- **Source:** https://github.com/pivoshenko/kasetto, https://dev.to/pivoshenko/kasetto-declarative-ai-agent-environment-manager-written-in-rust-34kf
- **Date:** 2026-04-12
- **Summary:** Rust binary supporting 21 agent presets. Single YAML config, content-hash diffing, 4 MCP config formats. Fetches skills from GitHub/GitLab/Bitbucket. Has `kst sync`, `kst list`, `kst doctor`, `kst clean` CLI.
- **Strengths:** 21 IDE presets with correct directory mappings; content-addressed caching; 4 MCP format handlers (mcpServers JSON, VS Code, OpenCode, Codex TOML); single binary, no runtime deps; private repo auth via env tokens.
- **Gaps (our differentiators):**
  - No hooks management (explicitly on roadmap, not implemented)
  - No agent config management (CLAUDE.md, AGENTS.md, .cursorrules)
  - No hybrid packages — a repo is either "skills" or "mcps"
  - No inline MCP declarations — MCPs must come from a git repo
  - No security review gate — Issue #15: untrusted repos become executable MCP config without approval
  - No conditional/optional dependencies
  - No skill auto-discovery from packages (must specify which skills to install)
  - No deployment lifecycle hooks (pre-install, post-deploy)
  - No project context system (AGENTS.md/PLANS.md/FINDINGS.md)
- **Architecture:** `src/` has modules for `bin/`, `commands/`, `fsops/`, `home/`, `list/`, `mcps/`, `model/`, `source/`. Model layer has `agent.rs` (21 presets), `config.rs` (YAML schema), `types.rs`. MCP merge logic in `mcps/mod.rs` supports 4 formats. Does NOT overwrite existing MCP keys (preserves local configs/secrets).

### Agent ecosystem landscape (2026)
- **Source:** Web search, 2026-04-12
- **Summary:** Key tools in this space:
  - **APM (Microsoft)** — `apm-cli`, resolves dependency trees, lockfiles. Buggy: no dedup, misclassifies hybrid packages.
  - **Kasetto** — see above. Closest to what we're building.
  - **Skills CLI (Vercel Labs)** — `npx skills add`. Skills-only, no MCP management. Installs to `~/.agents/skills/`.
  - **Killer-Skills** — directory + CLI for community skills. Cross-IDE format conversion. No MCP management.
  - **AGENTS.md convention** — emerging standard for shared agent context, with symlinks to tool-specific files.

### APM bugs and limitations
- **Source:** Direct observation, 2026-04-12
- **Date:** 2026-04-12
- **Summary:**
  1. **Hook duplication:** `.cursor/hooks.json` contains 84 entries (42 `sessionStart` + 42 `SessionStart`), all identical. APM appends without checking for existing entries. The hook runs 42x per session start.
  2. **Hybrid package misclassification:** `obra/superpowers` is classified as `hook_package` in `apm.lock.yaml`. This means only hooks are deployed. The 14 skills (`skills/*/SKILL.md`), 3 commands (`commands/*.md`), and 1 agent (`agents/code-reviewer.md`) are fetched but never compiled or deployed.
  3. **Orphaned files:** `apm_modules/` contains stale directories (`chrisboden/`, `modelcontextprotocol/`, `filesystem-mcp/`) with no cleanup mechanism.
  4. **No MCP deployment:** APM declares MCP servers in the manifest but doesn't actually sync them to IDE config files. `deploy.sh` handles all MCP deployment.
  5. **No inline MCPs:** Every MCP must be a git repository. Simple `npx` MCPs require unnecessary repo wrappers.

### planning-with-files skill analysis
- **Source:** https://github.com/OthmanAdi/planning-with-files
- **Date:** 2026-03-22
- **Summary:** Community skill (v2.26.1) implementing Manus-style file-based planning with three files (task_plan.md, findings.md, progress.md). Key strengths borrowed into context-harness: auto-recovery hooks (UserPromptSubmit, PostToolUse), FINDINGS.md separation for security, 2-Action Rule, Read Before Decide, 3-Strike Error Protocol. Task-centric (per-task) vs our project-centric (long-lived) approach.

### find-skills ecosystem
- **Source:** https://github.com/vercel-labs/skills
- **Date:** 2026-03-22
- **Summary:** Canonical find-skills is at `vercel-labs/skills@find-skills`, installed via `npx skills add`. `chrisboden/find-skills` is NOT a valid package (just a README catalog). The skills CLI (`npx skills`) is a separate ecosystem from APM — deploys to `~/.agents/skills/` with symlinks into IDE skill dirs.

## Discoveries

- **Observation:** APM and skills CLI coexist without conflict
  **Evidence:** APM deploys to project `.claude/skills/`, skills CLI deploys to `~/.agents/skills/` with symlinks into `~/.claude/skills/`. No path collisions.
  **Impact:** Can use both package managers freely based on package availability.

- **Observation:** Hooks in SKILL.md YAML frontmatter are auto-executed by Claude Code
  **Evidence:** After deploying updated context-harness with hooks, the UserPromptSubmit hook fired successfully on next prompt (showed PLANS.md status and FINDINGS.md tail).
  **Impact:** No need for separate settings.json hook configuration for skill-defined hooks.

- **Observation:** APM resolves GitHub dependencies directly without needing a local path override
  **Evidence:** Set `fantasy-cc/context-harness` in `apm.yml`, and `apm install` dynamically pulled it into `.github/skills`.
  **Impact:** Enables smooth extraction of custom generic skills to public Github packages.

- **Observation:** `deploy.sh` MCP merge preserves servers not listed in the manifest
  **Evidence:** Merge script reads existing JSON and updates entries by name from YAML; no deletion pass.
  **Impact:** Manual MCP entries survive deploy cycles.

- **Observation:** Claude Code user-scoped MCP servers live in `~/.claude.json`, not `~/.claude/.mcp.json`
  **Evidence:** `claude mcp add --scope user ...` writes to `~/.claude.json`.
  **Impact:** Automation must target `~/.claude.json` for reproducible Claude MCP setup.

- **Observation:** Kasetto's MCP merge does not overwrite existing keys
  **Evidence:** Source code comment in `mcps/mod.rs`: "Merge mcp config does not overwrite existing key"
  **Impact:** Nexus should follow the same pattern — preserve local MCP configs/secrets during merge.

- **Observation:** obra/superpowers hooks inject `using-superpowers/SKILL.md` content at session start via stdout
  **Evidence:** `hooks/session-start` bash script reads the skill file, JSON-escapes it, and outputs `{ "hookSpecificOutput": { "additionalContext": "..." } }` for Claude Code or `{ "additional_context": "..." }` for Cursor.
  **Impact:** Nexus hook aggregation must preserve the hook script execution paths (relative to package cache directory).

## Error Log
| Error | Context | Attempt | Resolution | Date |
|-------|---------|---------|------------|------|
| `chrisboden/find-skills` install failed | `apm install` — "Not a valid APM package" | 1: checked repo — no SKILL.md, just README | Removed from apm.yml; installed canonical version via `npx skills add vercel-labs/skills@find-skills -g -y` | 2026-03-22 |
